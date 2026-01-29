"""Utilities for Helm chart generation."""

import os
from pathlib import Path
from typing import Dict, Any, List

from rich.console import Console

console = Console()


def create_helm_template_files(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create Helm template files with direct string replacement.

    This function handles the creation of Helm template files separately from
    other templates because Helm uses the same double curly brace syntax as
    Jinja2, which causes conflicts.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    # Create helpers file
    create_helpers_tpl(project_dir, context)

    # Create other Helm template files
    create_deployment_yaml(project_dir, context)
    create_service_yaml(project_dir, context)
    create_serviceaccount_yaml(project_dir, context)
    create_ingress_yaml(project_dir, context)
    create_poddisruptionbudget_yaml(project_dir, context)
    create_hpa_yaml(project_dir, context)


def create_helpers_tpl(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the _helpers.tpl file for Helm.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    name = context["name"]

    helpers_content = f"""{{{{/* Helm helpers for {name} */}}}}

{{{{/* Expand the name of the chart. */}}}}
{{{{- define "{name}.name" -}}}}
{{{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}

{{{{/* Create a default fully qualified app name. */}}}}
{{{{- define "{name}.fullname" -}}}}
{{{{- if .Values.fullnameOverride }}}}
{{{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- $name := default .Chart.Name .Values.nameOverride }}}}
{{{{- if contains $name .Release.Name }}}}
{{{{- .Release.Name | trunc 63 | trimSuffix "-" }}}}
{{{{- else }}}}
{{{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}
{{{{- end }}}}
{{{{- end }}}}

{{{{/* Create chart name and version as used by the chart label. */}}}}
{{{{- define "{name}.chart" -}}}}
{{{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}}}
{{{{- end }}}}

{{{{/* Common labels */}}}}
{{{{- define "{name}.labels" -}}}}
helm.sh/chart: {{{{ include "{name}.chart" . }}}}
{{{{ include "{name}.selectorLabels" . }}}}
{{{{- if .Chart.AppVersion }}}}
app.kubernetes.io/version: {{{{ .Chart.AppVersion | quote }}}}
{{{{- end }}}}
app.kubernetes.io/managed-by: {{{{ .Release.Service }}}}
{{{{- end }}}}

{{{{/* Selector labels */}}}}
{{{{- define "{name}.selectorLabels" -}}}}
app.kubernetes.io/name: {{{{ include "{name}.name" . }}}}
app.kubernetes.io/instance: {{{{ .Release.Name }}}}
{{{{- end }}}}

{{{{/* Create the name of the service account to use */}}}}
{{{{- define "{name}.serviceAccountName" -}}}}
{{{{- if .Values.serviceAccount.create }}}}
{{{{- default (include "{name}.fullname" .) .Values.serviceAccount.name }}}}
{{{{- else }}}}
{{{{- default "default" .Values.serviceAccount.name }}}}
{{{{- end }}}}
{{{{- end }}}}
"""

    helpers_path = project_dir / "deployment/helm/templates/_helpers.tpl"
    helpers_path.write_text(helpers_content)


def create_deployment_yaml(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the deployment.yaml file for Helm.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    name = context["name"]

    content = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "%s.fullname" . }}
  labels:
    {{- include "%s.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "%s.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "%s.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "%s.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          {{- if .Values.env }}
          env:
            {{- toYaml .Values.env | nindent 12 }}
          {{- end }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            timeoutSeconds: 5
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            timeoutSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.topologySpreadConstraints }}
      topologySpreadConstraints:
        {{- toYaml . | nindent 8 }}
      {{- end }}
""" % (name, name, name, name, name)

    deployment_path = project_dir / "deployment/helm/templates/deployment.yaml"
    deployment_path.write_text(content)


def create_service_yaml(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the service.yaml file for Helm.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    name = context["name"]

    content = """apiVersion: v1
kind: Service
metadata:
  name: {{ include "%s.fullname" . }}
  labels:
    {{- include "%s.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
      name: http
  selector:
    {{- include "%s.selectorLabels" . | nindent 4 }}
""" % (name, name, name)

    service_path = project_dir / "deployment/helm/templates/service.yaml"
    service_path.write_text(content)


def create_serviceaccount_yaml(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the serviceaccount.yaml file for Helm.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    name = context["name"]

    content = """{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "%s.serviceAccountName" . }}
  labels:
    {{- include "%s.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
""" % (name, name)

    serviceaccount_path = project_dir / "deployment/helm/templates/serviceaccount.yaml"
    serviceaccount_path.write_text(content)


def create_ingress_yaml(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the ingress.yaml file for Helm.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    content = """{{- if .Values.ingress.enabled -}}
{{- $fullName := include "%s.fullname" . -}}
{{- $svcPort := .Values.service.port -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ $fullName }}
  labels:
    {{- include "%s.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ $fullName }}
                port:
                  number: {{ $svcPort }}
          {{- end }}
    {{- end }}
{{- end }}
""" % (context["name"], context["name"])

    ingress_path = project_dir / "deployment/helm/templates/ingress.yaml"
    ingress_path.write_text(content)


def create_poddisruptionbudget_yaml(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the poddisruptionbudget.yaml file for Helm.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    name = context["name"]

    content = """{{- if .Values.podDisruptionBudget.enabled }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "%s.fullname" . }}
  labels:
    {{- include "%s.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      {{- include "%s.selectorLabels" . | nindent 6 }}
  {{- if .Values.podDisruptionBudget.minAvailable }}
  minAvailable: {{ .Values.podDisruptionBudget.minAvailable }}
  {{- end }}
  {{- if .Values.podDisruptionBudget.maxUnavailable }}
  maxUnavailable: {{ .Values.podDisruptionBudget.maxUnavailable }}
  {{- end }}
{{- end }}
""" % (name, name, name)

    pdb_path = project_dir / "deployment/helm/templates/poddisruptionbudget.yaml"
    pdb_path.write_text(content)


def create_hpa_yaml(project_dir: Path, context: Dict[str, Any]) -> None:
    """Create the hpa.yaml file for Helm.

    Args:
        project_dir: Base directory for the project.
        context: Dictionary of context variables.
    """
    name = context["name"]

    content = """{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "%s.fullname" . }}
  labels:
    {{- include "%s.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "%s.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
""" % (name, name, name)

    hpa_path = project_dir / "deployment/helm/templates/hpa.yaml"
    hpa_path.write_text(content)