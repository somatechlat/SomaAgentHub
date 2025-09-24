import http from 'k6/http'
import { check, sleep } from 'k6'

export const options = {
  scenarios: {
    gateway: {
      executor: 'constant-vus',
      vus: 20,
      duration: '45s'
    },
    slm_sync: {
      executor: 'constant-vus',
      vus: 10,
      duration: '45s',
      startTime: '5s'
    },
    slm_embed: {
      executor: 'constant-vus',
      vus: 5,
      duration: '45s',
      startTime: '5s'
    }
  }
}

const headers = {
  'X-Tenant-ID': 'demo',
  'X-Client-Type': 'load-test',
  'X-Deployment-Mode': 'developer-light'
}

export default function () {
  const statusRes = http.get('http://localhost:8080/v1/status', { headers })
  check(statusRes, {
    'status 200': (r) => r.status === 200,
  })

  const inferRes = http.post('http://localhost:8700/v1/infer_sync', JSON.stringify({ prompt: 'Summarize onboarding checklist', model: 'stub' }), {
    headers: { 'Content-Type': 'application/json' }
  })
  check(inferRes, {
    'infer 200': (r) => r.status === 200,
  })

  const embedRes = http.post('http://localhost:8700/v1/embedding', JSON.stringify({ text: 'ACME invoice plan', model: 'stub-embedding' }), {
    headers: { 'Content-Type': 'application/json' }
  })
  check(embedRes, {
    'embedding 200': (r) => r.status === 200,
  })

  sleep(1)
}
