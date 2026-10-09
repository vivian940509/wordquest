const countdown=document.querySelector('[data-countdown]');
if(countdown){let v=Number(countdown.dataset.countdown||20);const t=setInterval(()=>{v--;countdown.textContent=String(Math.max(v,0));if(v<=0)clearInterval(t)},1000)}

const speechButton=document.querySelector('.speech-button');
if(speechButton){const target=speechButton.dataset.speechTarget||'';const speechValue=document.querySelector('#speechValue');const speechScore=document.querySelector('#speechScore');const feedback=document.querySelector('#speechFeedback');const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;speechButton.addEventListener('click',()=>{if(!Recognition){feedback.textContent='此瀏覽器不支援語音辨識，可改用 Chrome。';return}const r=new Recognition();r.lang='en-US';r.interimResults=false;speechButton.classList.add('listening');speechButton.textContent='聽你朗讀中...';r.onresult=e=>{const tr=e.results[0][0].transcript||'';speechValue.value=tr;const a=target.toLowerCase().split(/\s+/),b=tr.toLowerCase().split(/\s+/);let same=0;a.forEach(w=>{if(b.includes(w.replace(/[.,!?]/g,'')))same++});const score=Math.round(100*same/Math.max(a.length,1));speechScore.value=score;feedback.textContent=score>=90?'很接近！節奏和單字都很穩。':score>=75?'很接近，再慢一點會更清楚。':score>=55?'有抓到大部分內容，試著每個字分開唸。':'再慢一點，注意 th、r、v 等音。';speechButton.textContent=`辨識到：${tr}`;speechButton.classList.remove('listening')};r.onerror=()=>{feedback.textContent='辨識失敗，請再試一次。';speechButton.classList.remove('listening')};r.start()})}

document.querySelectorAll('[data-speak-word]').forEach(btn=>btn.addEventListener('click',()=>{const w=btn.dataset.speakWord||'';if(!('speechSynthesis'in window)||!w)return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(w);u.lang='en-US';u.rate=.82;window.speechSynthesis.speak(u)}));

const aiButton=document.querySelector('[data-ai-explain]');
if(aiButton){const box=document.querySelector('[data-ai-answer]');aiButton.addEventListener('click',async()=>{aiButton.disabled=true;aiButton.textContent='老師思考中…';try{const r=await fetch('/api/teacher/explain',{method:'POST',headers:{'Accept':'application/json'}});const data=await r.json();box.hidden=false;box.textContent=data.explanation||data.error||'暫時無法產生解說。';}catch(e){box.hidden=false;box.textContent='連線失敗，請稍後再試。';}finally{aiButton.disabled=false;aiButton.textContent='再解釋一次';}})}

const navToggle=document.querySelector('[data-nav-toggle]');
const nav=document.querySelector('[data-nav]');
if(navToggle&&nav){navToggle.addEventListener('click',()=>nav.classList.toggle('open'))}
