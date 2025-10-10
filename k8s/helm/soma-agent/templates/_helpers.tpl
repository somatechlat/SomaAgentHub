{{/* Helper templates for soma-agent chart */}}
{{- define "soma-agent.valuesChecksum" -}}
{{- toYaml .Values | sha256sum -}}
{{- end -}}
