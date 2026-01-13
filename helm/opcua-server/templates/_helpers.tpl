{{/*
Expand the name of the chart.
*/}}
{{- define "emberburn.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "emberburn.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "emberburn.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "emberburn.labels" -}}
helm.sh/chart: {{ include "emberburn.chart" . }}
{{ include "emberburn.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "emberburn.selectorLabels" -}}
app.kubernetes.io/name: {{ include "emberburn.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: emberburn
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "emberburn.serviceAccountName" -}}
{{- if .Values.pod.serviceAccount.create }}
{{- default (include "emberburn.fullname" .) .Values.pod.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.pod.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the namespace
*/}}
{{- define "emberburn.namespace" -}}
{{- .Values.namespace.name | default .Release.Namespace }}
{{- end }}

{{/*
Get resource requests and limits based on preset
*/}}
{{- define "emberburn.resources" -}}
{{- $preset := .Values.emberburn.resources.preset }}
{{- if eq $preset "custom" }}
{{- toYaml .Values.emberburn.resources.custom }}
{{- else }}
{{- $presets := .Values.emberburn.resources.presets }}
{{- if hasKey $presets $preset }}
{{- toYaml (index $presets $preset) }}
{{- else }}
{{- toYaml $presets.medium }}
{{- end }}
{{- end }}
{{- end }}

{{/*
PVC name
*/}}
{{- define "emberburn.pvcName" -}}
{{- printf "%s-data" (include "emberburn.fullname" .) }}
{{- end }}

{{/*
ConfigMap name for tags
*/}}
{{- define "emberburn.tagsConfigMapName" -}}
{{- printf "%s-tags" (include "emberburn.fullname" .) }}
{{- end }}

{{/*
ConfigMap name for publishers
*/}}
{{- define "emberburn.publishersConfigMapName" -}}
{{- printf "%s-publishers" (include "emberburn.fullname" .) }}
{{- end }}

{{/*
Generate JSON config for tags
*/}}
{{- define "emberburn.tagsConfig" -}}
{{- toJson .Values.config.tags }}
{{- end }}

{{/*
Generate JSON config for publishers
*/}}
{{- define "emberburn.publishersConfig" -}}
{{- toJson .Values.config.publishers }}
{{- end }}
