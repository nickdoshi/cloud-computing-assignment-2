// Swap this URL to point at whichever backend you are demoing.
// EC2:     'http://54.162.84.110'
// ECS:     'http://3.86.226.187:8080'
// Lambda:  'https://ghp10za5f0.execute-api.us-east-1.amazonaws.com/test'
const BACKEND_URL = '';

function unwrapApiResponse(data) {
    if (data && typeof data === 'object' && 'statusCode' in data && 'body' in data) {
        if (typeof data.body === 'string') {
            return data.body ? JSON.parse(data.body) : {};
        }
        return data.body || {};
    }
    return data;
}
