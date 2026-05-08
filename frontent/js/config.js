// Swap this URL to point at whichever backend you are demoing.
// EC2:     'http://34.207.102.74'
// ECS:     'http://3.86.226.187:8080'
// Lambda:  'https://ghp10za5f0.execute-api.us-east-1.amazonaws.com/test'
const BACKEND_URL = 'https://ghp10za5f0.execute-api.us-east-1.amazonaws.com/test';

function unwrapApiResponse(data) {
    if (data && typeof data === 'object' && 'statusCode' in data && 'body' in data) {
        if (typeof data.body === 'string') {
            return data.body ? JSON.parse(data.body) : {};
        }
        return data.body || {};
    }
    return data;
}
