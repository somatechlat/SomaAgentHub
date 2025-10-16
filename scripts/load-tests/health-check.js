import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m30s', target: 20 },
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function() {
  let res = http.get('http://gateway-api:10000/ready');
  check(res, {
    'gateway-api health status 200': (r) => r.status === 200,
  });

  res = http.get('http://orchestrator:10001/ready');
  check(res, {
    'orchestrator health status 200': (r) => r.status === 200,
  });

  res = http.get('http://identity-service:10002/ready');
  check(res, {
    'identity-service health status 200': (r) => r.status === 200,
  });

  sleep(1);
}
