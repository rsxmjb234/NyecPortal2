"""
Jira REST API helper — reads credentials from the MCP config so they
are never hardcoded. Delete this file when done with the session.

Usage:
    from _jira_api import jira_get, jira_put
    issue = jira_get('/rest/api/3/issue/IN-3737')
    jira_put('/rest/api/3/issue/IN-3737', {'fields': {'summary': 'New title'}})
"""
import json, os, base64
from urllib.request import urlopen, Request
from urllib.error import HTTPError

_CFG_PATH = os.path.join(os.environ['USERPROFILE'], '.kiro', 'settings', 'mcp.json')

def _creds():
    with open(_CFG_PATH) as f:
        cfg = json.load(f)
    env = cfg['mcpServers']['jira']['env']
    return env['JIRA_URL'], env['JIRA_USERNAME'], env['JIRA_TOKEN']

def _auth_header():
    url, user, token = _creds()
    b64 = base64.b64encode(f'{user}:{token}'.encode()).decode()
    return url, {'Authorization': f'Basic {b64}', 'Content-Type': 'application/json'}

def jira_get(path):
    url, headers = _auth_header()
    req = Request(url + path, headers=headers)
    with urlopen(req) as r:
        return json.loads(r.read())

def jira_put(path, body):
    url, headers = _auth_header()
    data = json.dumps(body).encode()
    req = Request(url + path, data=data, headers=headers, method='PUT')
    try:
        with urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {'status': r.status}
    except HTTPError as e:
        return {'error': e.code, 'body': e.read().decode()}

if __name__ == '__main__':
    # Quick test: read IN-3737
    issue = jira_get('/rest/api/3/issue/IN-3737?fields=summary,status')
    print(f"Key:     {issue['key']}")
    print(f"Summary: {issue['fields']['summary']}")
    print(f"Status:  {issue['fields']['status']['name']}")
