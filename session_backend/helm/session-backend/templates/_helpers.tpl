{{/*
Expand the name of the chart.
*/}}
{{- define "session-backend.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "session-backend.fullname" -}}
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
{{- define "session-backend.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "session-backend.labels" -}}
helm.sh/chart: {{ include "session-backend.chart" . }}
{{ include "session-backend.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "session-backend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "session-backend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "session-backend.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "session-backend.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL fullname
*/}}
{{- define "session-backend.postgresql.fullname" -}}
{{- printf "%s-postgresql" (include "session-backend.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "session-backend.postgresql.host" -}}
{{- if .Values.postgresql.enabled }}
{{- include "session-backend.postgresql.fullname" . }}
{{- else }}
{{- .Values.externalPostgresql.host }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port
*/}}
{{- define "session-backend.postgresql.port" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.service.port }}
{{- else }}
{{- .Values.externalPostgresql.port }}
{{- end }}
{{- end }}

{{/*
PostgreSQL database
*/}}
{{- define "session-backend.postgresql.database" -}}
{{- if .Values.postgresql.enabled }}
{{- .Values.postgresql.auth.database }}
{{- else }}
{{- .Values.externalPostgresql.database }}
{{- end }}
{{- end }}

{{/*
PostgreSQL secret name
*/}}
{{- define "session-backend.postgresql.secretName" -}}
{{- if .Values.postgresql.enabled }}
{{- include "session-backend.postgresql.fullname" . }}
{{- else }}
{{- .Values.externalPostgresql.existingSecret }}
{{- end }}
{{- end }}
