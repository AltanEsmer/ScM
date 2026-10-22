// Offline fixture only. This process has no credentials and never forwards traffic.
import http from 'node:http';
import {readFileSync} from 'node:fs';
import {authFromJSON,forward} from './live_transport.mjs';
export function validate(path, body) {
 if(path!=='/v1/responses')throw Error('path');
 if(body.model!=='gpt-6.1-sol')throw Error('model');
 if(body.reasoning?.effort!=='medium')throw Error('effort');
 if(!Array.isArray(body.tools))throw Error('tools_missing');
 if(body.tools.length!==0)throw Error('tool');
 if(body.previous_response_id)throw Error('history');
 if(body.input?.some(i=>['function_call_output','computer_call_output','mcp_call','function_call'].includes(i.type)))throw Error('tool_output');
 return true;
}
if(process.argv[2]==='selftest') {
 const good={model:'gpt-6.1-sol',reasoning:{effort:'medium'},tools:[],input:[]};
 const bad=[['/x',good],['/v1/responses',{...good,model:'other'}],['/v1/responses',{...good,reasoning:{effort:'low'}}],['/v1/responses',{...good,tools:[{type:'web_search'}]}],['/v1/responses',{...good,tools:[{type:'function',name:'exec_command'}]}],['/v1/responses',{...good,tools:[{type:'function',name:'current_time'}]}],['/v1/responses',{...good,input:[{type:'function_call_output'}]}]];
 validate('/v1/responses',good);for(const [p,b]of bad){let rejected=false;try{validate(p,b)}catch{rejected=true}if(!rejected)throw Error('accepted invalid request')};console.log(JSON.stringify({policy_tests:bad.length+1,ok:true}));
} else {
 const live=process.argv[2]==='live';
 const auth=live?authFromJSON(JSON.parse(readFileSync(0,'utf8'))):null;
 let attempted=false;
 http.createServer((req,res)=>{let data='';req.on('data',chunk=>{data+=chunk;if(data.length>2000000)req.destroy()});req.on('end',()=>{let body;try{if(req.method!=='POST')throw Error('method');body=JSON.parse(data);validate(req.url,body)}catch(error){console.log(JSON.stringify({kind:'rejected',path:req.url,reason:error.message}));res.writeHead(403);res.end('rejected');return}
 if(live){if(attempted){res.writeHead(403);res.end('no retry');return}attempted=true;forward(body,auth).then(({data,reportedModel})=>{console.log(JSON.stringify({kind:'live_forwarded',requested_model:body.model,reported_model:reportedModel,effort:body.reasoning.effort,tools:body.tools}));res.writeHead(200,{'content-type':'text/event-stream'});res.end(data)}).catch(error=>{console.log(JSON.stringify({kind:'live_failed',reason:error.message}));res.writeHead(502);res.end('live transport failed closed')});return}
 console.log(JSON.stringify({kind:'capture',method:req.method,path:req.url,body}));
 // Protocol fixture, not a model answer or candidate. Tests require this exact marker.
 const response={id:'resp_offline_fixture',object:'response',created_at:0,status:'completed',model:'gpt-6.1-sol',output:[{type:'message',id:'msg_offline_fixture',status:'completed',role:'assistant',content:[{type:'output_text',text:'OFFLINE_OK',annotations:[]}]}],usage:{input_tokens:1,output_tokens:1,total_tokens:2}};
 res.writeHead(200,{'content-type':'text/event-stream'});
 for(const event of [{type:'response.created',response:{...response,status:'in_progress',output:[]}},{type:'response.output_item.added',output_index:0,item:response.output[0]},{type:'response.output_text.delta',item_id:'msg_offline_fixture',output_index:0,content_index:0,delta:'OFFLINE_OK'},{type:'response.output_item.done',output_index:0,item:response.output[0]},{type:'response.completed',response}])res.write(`event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`);
 res.end();});}).listen(8080,'0.0.0.0',()=>console.log(JSON.stringify({kind:'ready'})));
}
