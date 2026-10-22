// No host files, credentials, sessions, or project configuration are inputs.
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import net from 'node:net';
const offlinePrompt = 'OFFLINE_ISOLATION_FIXTURE: Return the literal text OFFLINE_OK.';
const live = process.env.ISOLATION_MODE === 'live';
const prompt = live ? (await import('node:fs')).readFileSync(0,'utf8') : offlinePrompt;
let answer = '';
if (process.argv[2] === 'canary') {
  const fs = await import('node:fs');
  const checks = {};
  for (const path of ['/reference-canary', '/tests-canary', '/old-answers-canary', '/var/run/docker.sock', '/Users', '/root/.codex/auth.json']) checks[path] = fs.existsSync(path);
  const probe = (host,port=443) => new Promise(resolve => { const s = net.connect({host,port}); s.setTimeout(1500); s.on('connect',()=>{s.destroy();resolve(false)}); s.on('error',()=>resolve(true)); s.on('timeout',()=>{s.destroy();resolve(true)}); });
  const blocked = await probe('1.1.1.1');
  const hostBlocked = await probe('host.docker.internal',Number(process.env.SCM_HOST_PROBE_PORT));
  console.log(JSON.stringify({files:checks, direct_external_blocked:blocked,host_gateway_blocked:hostBlocked,uid:process.getuid()}));
  process.exit(Object.values(checks).some(Boolean)||!blocked||!hostBlocked||process.getuid()===0?1:0);
}
mkdirSync('/tmp/codex', {recursive:true});
const config = {
 model_provider:'isolation',model:'gpt-6.1-sol',model_reasoning_effort:'medium',
 'model_providers.isolation.name':'Offline isolation fixture',
 'model_providers.isolation.base_url':'http://relay:8080/v1',
 'model_providers.isolation.wire_api':'responses',
 'model_providers.isolation.env_key':'ISOLATION_DUMMY_TOKEN',
 'model_providers.isolation.supports_websockets':false,
 'model_providers.isolation.request_max_retries':0,
 'model_providers.isolation.stream_max_retries':0,
 web_search:'disabled',project_doc_max_bytes:0,
 'skills.include_instructions':false,'skills.bundled.enabled':false,
 'tools.update_plan.enabled':false,'tools.experimental_request_user_input.enabled':false,
 'features.shell_tool':false,'features.multi_agent':false,'features.apps':false,
 'features.plugins':false,'features.remote_plugin':false,'features.browser_use':false,
 'features.computer_use':false,'features.in_app_browser':false,'features.image_generation':false,
 'features.sleep_tool':false,'features.goals':false,'features.hooks':false,
 'features.code_mode_host':false,'features.skill_search':false,'features.tool_suggest':false,
 'features.workspace_dependencies':false,'features.daemon_auto_start':false,
 'check_for_update_on_startup':false,'analytics.enabled':false,
};
const args=['app-server','--stdio','--strict-config'];
for (const [k,v] of Object.entries(config)) args.push('-c',`${k}=${JSON.stringify(v)}`);
const child=spawn('codex',args,{env:{PATH:process.env.PATH,HOME:'/tmp/home',CODEX_HOME:'/tmp/codex',ISOLATION_DUMMY_TOKEN:'offline-not-a-credential'},stdio:['pipe','pipe','pipe']});
const pending=new Map(); let id=0, buffer='', finished=false;
function request(method,params){return new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});child.stdin.write(JSON.stringify({jsonrpc:'2.0',id:n,method,params})+'\n')})}
function stop(code,message){if(finished)return;finished=true;console.log(JSON.stringify({kind:'client_result',ok:code===0,message,...(code===0?{answer}: {})}));child.kill();setTimeout(()=>process.exit(code),20);}
child.stderr.on('data',()=>{}); // Do not publish unreviewed provider/client diagnostics.
child.on('error',()=>stop(1,'client_start_failed'));
child.on('exit',code=>{if(!finished)stop(1,`unexpected_client_exit_${code}`)});
child.stdout.on('data',data=>{buffer+=data;while(buffer.includes('\n')){const end=buffer.indexOf('\n');const line=buffer.slice(0,end);buffer=buffer.slice(end+1);let msg;try{msg=JSON.parse(line)}catch{continue}
 if(msg.id!==undefined&&pending.has(msg.id)){const p=pending.get(msg.id);pending.delete(msg.id);msg.error?p.reject(new Error(JSON.stringify(msg.error))):p.resolve(msg.result)}
 else if(msg.method==='item/completed' && msg.params.item.type==='agentMessage'){answer=msg.params.item.text;}
 else if(msg.method==='turn/completed'){const turn=msg.params.turn;stop(turn.status==='completed'?0:1,turn.status)}
 else if(msg.id!==undefined){child.stdin.write(JSON.stringify({jsonrpc:'2.0',id:msg.id,error:{code:-32601,message:'All client tool requests rejected'}})+'\n')}
}});
setTimeout(()=>stop(1,live?'live_timeout':'offline_timeout'),live?135000:45000).unref();
try {
 await request('initialize',{clientInfo:{name:'scm-isolation-offline',version:'1'},capabilities:{experimentalApi:true}});
 child.stdin.write(JSON.stringify({method:'initialized'})+'\n');
 const started=await request('thread/start',{model:'gpt-6.1-sol',modelProvider:'isolation',cwd:'/tmp',ephemeral:true,environments:[],dynamicTools:[],allowProviderModelFallback:false,approvalPolicy:'never',config:{model_reasoning_effort:'medium'}});
 console.log(JSON.stringify({kind:'thread_settings',model:started.model,effort:started.reasoningEffort,thread_id:started.thread.id}));
 await request('turn/start',{threadId:started.thread.id,input:[{type:'text',text:prompt}],model:'gpt-6.1-sol',effort:'medium',environments:[]});
} catch(error) {stop(1,'rpc_configuration_or_protocol_error:'+error.message)}
