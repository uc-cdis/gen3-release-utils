import http from 'k6/http';
import { sleep } from 'k6';

export default function () {
  http.get('https://npmjs.org', {
    tags: {
      test_run_id: '0',
      release: '20220411',
    }
  });
  sleep(1);
}