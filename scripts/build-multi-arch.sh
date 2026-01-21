#!/bin/bash
#
# Multi-Architecture Docker Build Script for EmberBurn
# Builds for AMD64 and ARM64 platforms
#
# Usage:
#   ./scripts/build-multi-arch.sh [OPTIONS]
#
# Options:
#   --push              Push images to registry after build
#   --tag TAG           Specify custom tag (default: latest)
#   --registry REG      Specify registry (default: ghcr.io/embernet-ai)
#   --platforms PLAT    Specify platforms (default: linux/amd64,linux/arm64)
#   --load              Load image to local Docker (single platform only)
#   --cache-from TYPE   Cache source (default: type=gha)
#   --cache-to TYPE     Cache destination (default: type=gha,mode=max)
#   --dry-run           Show commands without executing
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGISTRY="${REGISTRY:-ghcr.io/embernet-ai}"
IMAGE_NAME="${IMAGE_NAME:-emberburn}"
TAG="${TAG:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
PUSH=false
LOAD=false
DRY_RUN=false
CACHE_FROM="type=registry,ref=${REGISTRY}/${IMAGE_NAME}:buildcache"
CACHE_TO="type=registry,ref=${REGISTRY}/${IMAGE_NAME}:buildcache,mode=max"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --load)
            LOAD=true
            shift
            ;;
        --cache-from)
            CACHE_FROM="$2"
            shift 2
            ;;
        --cache-to)
            CACHE_TO="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            grep '^#' "$0" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validation
if [ "$LOAD" = true ] && [ "$PUSH" = true ]; then
    echo -e "${RED}Error: Cannot use --load and --push together${NC}"
    exit 1
fi

if [ "$LOAD" = true ] && [[ "$PLATFORMS" == *","* ]]; then
    echo -e "${YELLOW}Warning: --load requires single platform. Using linux/amd64${NC}"
    PLATFORMS="linux/amd64"
fi

# Build full image reference
IMAGE_REF="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  EmberBurn Multi-Arch Docker Build${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}Image:${NC}      ${IMAGE_REF}"
echo -e "${BLUE}Platforms:${NC}  ${PLATFORMS}"
echo -e "${BLUE}Push:${NC}       ${PUSH}"
echo -e "${BLUE}Load:${NC}       ${LOAD}"
echo -e "${BLUE}Cache From:${NC} ${CACHE_FROM}"
echo -e "${BLUE}Cache To:${NC}   ${CACHE_TO}"
echo ""

# Check for buildx
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker Buildx is not installed${NC}"
    echo "Install with: docker buildx install"
    exit 1
fi

# Create builder if it doesn't exist
BUILDER_NAME="emberburn-multi-arch"
if ! docker buildx inspect "$BUILDER_NAME" > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating buildx builder: ${BUILDER_NAME}${NC}"
    if [ "$DRY_RUN" = false ]; then
        docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap
    else
        echo "[DRY RUN] docker buildx create --name $BUILDER_NAME --driver docker-container --bootstrap"
    fi
fi

# Use the builder
echo -e "${BLUE}Using builder: ${BUILDER_NAME}${NC}"
if [ "$DRY_RUN" = false ]; then
    docker buildx use "$BUILDER_NAME"
else
    echo "[DRY RUN] docker buildx use $BUILDER_NAME"
fi

# Build command
BUILD_CMD="docker buildx build"
BUILD_CMD="$BUILD_CMD --platform $PLATFORMS"
BUILD_CMD="$BUILD_CMD --tag $IMAGE_REF"
BUILD_CMD="$BUILD_CMD --cache-from $CACHE_FROM"
BUILD_CMD="$BUILD_CMD --cache-to $CACHE_TO"
BUILD_CMD="$BUILD_CMD --build-arg BUILDKIT_INLINE_CACHE=1"

# Add metadata labels
BUILD_CMD="$BUILD_CMD --label org.opencontainers.image.source=https://github.com/Embernet-ai/Small-Application"
BUILD_CMD="$BUILD_CMD --label org.opencontainers.image.description='EmberBurn Industrial IoT Gateway'"
BUILD_CMD="$BUILD_CMD --label org.opencontainers.image.version=$TAG"
BUILD_CMD="$BUILD_CMD --label org.opencontainers.image.created=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [ "$PUSH" = true ]; then
    BUILD_CMD="$BUILD_CMD --push"
elif [ "$LOAD" = true ]; then
    BUILD_CMD="$BUILD_CMD --load"
fi

BUILD_CMD="$BUILD_CMD ."

# Execute build
echo ""
echo -e "${YELLOW}Executing build command:${NC}"
echo "$BUILD_CMD"
echo ""

if [ "$DRY_RUN" = false ]; then
    eval "$BUILD_CMD"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Build completed successfully!${NC}"
        echo ""
        
        if [ "$PUSH" = true ]; then
            echo -e "${GREEN}Image pushed to: ${IMAGE_REF}${NC}"
            echo ""
            echo "Pull with:"
            echo "  docker pull ${IMAGE_REF}"
        elif [ "$LOAD" = true ]; then
            echo -e "${GREEN}Image loaded to local Docker${NC}"
            echo ""
            echo "Run with:"
            echo "  docker run -p 4840:4840 -p 5000:5000 -p 8000:8000 ${IMAGE_REF}"
        fi
        
        echo ""
        echo "Platform manifest:"
        docker buildx imagetools inspect "${IMAGE_REF}" || true
    else
        echo ""
        echo -e "${RED}❌ Build failed!${NC}"
        exit 1
    fi
else
    echo "[DRY RUN] Command would be executed"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
