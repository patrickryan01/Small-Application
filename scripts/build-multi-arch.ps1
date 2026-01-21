#!/usr/bin/env pwsh
#
# Multi-Architecture Docker Build Script for EmberBurn (PowerShell)
# Builds for AMD64 and ARM64 platforms
#
# Usage:
#   .\scripts\build-multi-arch.ps1 [OPTIONS]
#
# Options:
#   -Push              Push images to registry after build
#   -Tag TAG           Specify custom tag (default: latest)
#   -Registry REG      Specify registry (default: ghcr.io/embernet-ai)
#   -Platforms PLAT    Specify platforms (default: linux/amd64,linux/arm64)
#   -Load              Load image to local Docker (single platform only)
#   -DryRun            Show commands without executing
#

param(
    [switch]$Push = $false,
    [string]$Tag = "latest",
    [string]$Registry = "ghcr.io/embernet-ai",
    [string]$ImageName = "emberburn",
    [string]$Platforms = "linux/amd64,linux/arm64",
    [switch]$Load = $false,
    [switch]$DryRun = $false,
    [switch]$Help = $false
)

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Show help
if ($Help) {
    Get-Content $PSCommandPath | Select-String "^#" | ForEach-Object { $_.Line.Substring(2) }
    exit 0
}

# Validation
if ($Load -and $Push) {
    Write-ColorOutput "Error: Cannot use -Load and -Push together" "Red"
    exit 1
}

if ($Load -and $Platforms.Contains(",")) {
    Write-ColorOutput "Warning: -Load requires single platform. Using linux/amd64" "Yellow"
    $Platforms = "linux/amd64"
}

# Build full image reference
$ImageRef = "${Registry}/${ImageName}:${Tag}"

Write-Host ""
Write-ColorOutput "=========================================" "Green"
Write-ColorOutput "  EmberBurn Multi-Arch Docker Build" "Green"
Write-ColorOutput "=========================================" "Green"
Write-Host ""
Write-ColorOutput "Image:      $ImageRef" "Cyan"
Write-ColorOutput "Platforms:  $Platforms" "Cyan"
Write-ColorOutput "Push:       $Push" "Cyan"
Write-ColorOutput "Load:       $Load" "Cyan"
Write-Host ""

# Check for buildx
try {
    docker buildx version | Out-Null
} catch {
    Write-ColorOutput "Error: Docker Buildx is not installed" "Red"
    Write-ColorOutput "Install with: docker buildx install" "Yellow"
    exit 1
}

# Create builder if it doesn't exist
$BuilderName = "emberburn-multi-arch"
$builderExists = docker buildx inspect $BuilderName 2>$null
if (-not $builderExists) {
    Write-ColorOutput "Creating buildx builder: $BuilderName" "Yellow"
    if (-not $DryRun) {
        docker buildx create --name $BuilderName --driver docker-container --bootstrap
    } else {
        Write-ColorOutput "[DRY RUN] docker buildx create --name $BuilderName --driver docker-container --bootstrap" "Gray"
    }
}

# Use the builder
Write-ColorOutput "Using builder: $BuilderName" "Cyan"
if (-not $DryRun) {
    docker buildx use $BuilderName
} else {
    Write-ColorOutput "[DRY RUN] docker buildx use $BuilderName" "Gray"
}

# Build command arguments
$BuildArgs = @(
    "buildx", "build",
    "--platform", $Platforms,
    "--tag", $ImageRef,
    "--cache-from", "type=registry,ref=${Registry}/${ImageName}:buildcache",
    "--cache-to", "type=registry,ref=${Registry}/${ImageName}:buildcache,mode=max",
    "--build-arg", "BUILDKIT_INLINE_CACHE=1",
    "--label", "org.opencontainers.image.source=https://github.com/Embernet-ai/Small-Application",
    "--label", "org.opencontainers.image.description=EmberBurn Industrial IoT Gateway",
    "--label", "org.opencontainers.image.version=$Tag",
    "--label", "org.opencontainers.image.created=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ' -AsUTC)"
)

if ($Push) {
    $BuildArgs += "--push"
} elseif ($Load) {
    $BuildArgs += "--load"
}

$BuildArgs += "."

# Execute build
Write-Host ""
Write-ColorOutput "Executing build command:" "Yellow"
Write-ColorOutput "docker $($BuildArgs -join ' ')" "Gray"
Write-Host ""

if (-not $DryRun) {
    & docker @BuildArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-ColorOutput "✅ Build completed successfully!" "Green"
        Write-Host ""
        
        if ($Push) {
            Write-ColorOutput "Image pushed to: $ImageRef" "Green"
            Write-Host ""
            Write-Host "Pull with:"
            Write-Host "  docker pull $ImageRef"
        } elseif ($Load) {
            Write-ColorOutput "Image loaded to local Docker" "Green"
            Write-Host ""
            Write-Host "Run with:"
            Write-Host "  docker run -p 4840:4840 -p 5000:5000 -p 8000:8000 $ImageRef"
        }
        
        Write-Host ""
        Write-Host "Platform manifest:"
        docker buildx imagetools inspect $ImageRef
    } else {
        Write-Host ""
        Write-ColorOutput "❌ Build failed!" "Red"
        exit 1
    }
} else {
    Write-ColorOutput "[DRY RUN] Command would be executed" "Gray"
}

Write-Host ""
Write-ColorOutput "Done!" "Green"
Write-Host ""
