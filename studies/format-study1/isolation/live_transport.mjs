// Official rust-v0.157.1 provider transport; no caller-selected destination.
import https from 'node:https';
export const DESTINATION = 'https://chatgpt.com/backend-api/codex/responses';
export function authFromJSON(value) {
  const {access_token:token,account_id:account} = value?.tokens ?? {};
  if(typeof token!=='string'||!token||typeof account!=='string'||!account||/[\r\n]/.test(token+account))throw Error('LOGIN_REQUIRED');
  // No refresh attempts or credential writes; an expired/rejected login fails closed.
  return {token,account};
}
export function forward(body,auth,request=https.request) {
  return new Promise((resolve,reject)=>{
    const upstream=request(DESTINATION,{method:'POST',headers:{
      authorization:`Bearer ${auth.token}`,'ChatGPT-Account-ID':auth.account,
      'content-type':'application/json',accept:'text/event-stream',
      originator:'codex_cli_rs','user-agent':'codex_cli_rs/0.157.1',
    }},response=>{
      if(response.statusCode!==200){response.resume();reject(Error(response.statusCode===401?'LOGIN_REQUIRED':'PROVIDER_REJECTED'));return}
      let data='';response.setEncoding('utf8');response.on('data',chunk=>{data+=chunk;if(data.length>16000000){response.destroy();reject(Error('RESPONSE_TOO_LARGE'))}});
      response.on('error',()=>reject(Error('PROVIDER_STREAM_FAILED')));
      response.on('end',()=>{
        const events=data.split('\n').filter(line=>line.startsWith('data: ')).flatMap(line=>{try{return[JSON.parse(line.slice(6))]}catch{return[]}});
        const completed=events.find(event=>event.type==='response.completed');
        const reported=completed?.response?.model;
        if(completed?.response?.output?.some(item=>!['message','reasoning'].includes(item.type))){reject(Error('UNEXPECTED_PROVIDER_TOOL_OUTPUT'));return}
        if(reported!=='gpt-6.1-sol'){reject(Error('MODEL_IDENTITY_UNVERIFIED'));return}
        if(events.some(event=>event.type==='response.failed'||event.type==='error')){reject(Error('PROVIDER_FAILED'));return}
        resolve({data,reportedModel:reported});
      });
    });
    upstream.on('error',()=>reject(Error('PROVIDER_CONNECTION_FAILED')));
    upstream.setTimeout(120000,()=>{upstream.destroy();reject(Error('PROVIDER_TIMEOUT'))});
    upstream.end(JSON.stringify(body));
  });
}
