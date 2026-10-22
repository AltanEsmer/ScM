import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {authFromJSON,forward,DESTINATION} from './live_transport.mjs';
const auth=authFromJSON({tokens:{access_token:'FAKE_TOKEN',account_id:'FAKE_ACCOUNT'}});
assert.throws(()=>authFromJSON({tokens:{access_token:'secret\r\nheader',account_id:'fake'}}));
assert.throws(()=>authFromJSON({}));
const body={model:'gpt-6.1-sol',reasoning:{effort:'medium'},tools:[]};
function mock(status,reported='gpt-6.1-sol') {
  return (url,options,callback)=>{
    assert.equal(url,DESTINATION);
    assert.equal(url,'https://chatgpt.com/backend-api/codex/responses');
    assert.equal(options.headers.authorization,'Bearer FAKE_TOKEN');
    assert.equal(options.headers['ChatGPT-Account-ID'],'FAKE_ACCOUNT');
    assert.equal(options.method,'POST');
    assert.equal(options.headers.originator,'codex_cli_rs');
    assert.equal(options.headers['user-agent'],'codex_cli_rs/0.157.1');
    const request=new EventEmitter();request.setTimeout=()=>{};request.destroy=()=>{};
    request.end=payload=>{
      assert.deepEqual(JSON.parse(payload),body);
      queueMicrotask(()=>{
        const response=new EventEmitter();response.statusCode=status;response.resume=()=>{};response.setEncoding=()=>{};
        callback(response);
        response.emit('data',`data: ${JSON.stringify({type:'response.completed',response:{model:reported}})}\n\n`);
        response.emit('end');
      });
    };
    return request;
  };
}
assert.equal((await forward(body,auth,mock(200))).reportedModel,'gpt-6.1-sol');
await assert.rejects(forward(body,auth,mock(302)),/PROVIDER_REJECTED/);
await assert.rejects(forward(body,auth,mock(401)),/LOGIN_REQUIRED/);
await assert.rejects(forward(body,auth,mock(200,'different-model')),/MODEL_IDENTITY_UNVERIFIED/);
await assert.rejects(forward(body,auth,mock(200,null)),/MODEL_IDENTITY_UNVERIFIED/);
console.log('mock HTTPS/auth tests passed: 7; network requests: 0');
