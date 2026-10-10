const countdown=document.querySelector('[data-countdown]');
if(countdown){let v=Number(countdown.dataset.countdown||10);const form=document.querySelector('[data-answer-form]');let submitted=false;if(form)form.addEventListener('submit',()=>{submitted=true});const t=setInterval(()=>{v--;countdown.textContent=String(Math.max(v,0));if(v<=5)countdown.classList.add('urgent');if(v<=0){clearInterval(t);if(form&&!submitted){submitted=true;form.querySelectorAll('button').forEach(b=>b.disabled=true);form.requestSubmit();}}},1000)}

const speechButton=document.querySelector('.speech-button');
if(speechButton){const target=speechButton.dataset.speechTarget||'';const speechValue=document.querySelector('#speechValue');const speechScore=document.querySelector('#speechScore');const feedback=document.querySelector('#speechFeedback');const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;speechButton.addEventListener('click',()=>{if(!Recognition){feedback.textContent='此瀏覽器不支援語音辨識，可改用 Chrome。';return}const r=new Recognition();r.lang='en-US';r.interimResults=false;speechButton.classList.add('listening');speechButton.textContent='聽你朗讀中...';r.onresult=e=>{const tr=e.results[0][0].transcript||'';speechValue.value=tr;const a=target.toLowerCase().split(/\s+/),b=tr.toLowerCase().split(/\s+/);let same=0;a.forEach(w=>{if(b.includes(w.replace(/[.,!?]/g,'')))same++});const score=Math.round(100*same/Math.max(a.length,1));speechScore.value=score;feedback.textContent=score>=90?'很接近！節奏和單字都很穩。':score>=75?'很接近，再慢一點會更清楚。':score>=55?'有抓到大部分內容，試著每個字分開唸。':'再慢一點，注意 th、r、v 等音。';speechButton.textContent=`辨識到：${tr}`;speechButton.classList.remove('listening')};r.onerror=()=>{feedback.textContent='辨識失敗，請再試一次。';speechButton.classList.remove('listening')};r.start()})}

const speakWithBrowser=(word)=>new Promise((resolve,reject)=>{
  if(!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance){reject(new Error('tts unavailable'));return}
  try{
    window.speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(word);
    u.lang='en-US';u.rate=.82;u.volume=1;
    u.onend=()=>resolve();u.onerror=()=>reject(new Error('tts failed'));
    // Android WebView/Chrome can pause the synthesizer after page navigation.
    window.speechSynthesis.resume();
    window.speechSynthesis.speak(u);
  }catch(e){reject(e)}
});

const playPronunciation=async(btn)=>{
  const word=(btn.dataset.speakWord||'').trim();
  if(!word)return;
  const original=btn.textContent;
  btn.disabled=true;btn.classList.add('speaking');btn.textContent='播放中…';
  let played=false;
  try{
    const r=await fetch(`/api/pronounce?word=${encodeURIComponent(word)}`,{headers:{'Accept':'application/json'}});
    if(r.ok){
      const data=await r.json();
      if(data.audio){
        await new Promise((resolve,reject)=>{
          const audio=new Audio(data.audio);
          audio.preload='auto';audio.volume=1;
          audio.onended=()=>resolve();audio.onerror=()=>reject(new Error('audio failed'));
          const p=audio.play();if(p&&p.catch)p.catch(reject);
        });
        played=true;
      }
    }
  }catch(e){}
  if(!played){
    try{await speakWithBrowser(word);played=true}catch(e){}
  }
  btn.disabled=false;btn.classList.remove('speaking');btn.textContent=played?original:'手機無法播放，請確認媒體音量';
  if(!played)setTimeout(()=>{btn.textContent=original},2200);
};

document.querySelectorAll('[data-speak-word]').forEach(btn=>btn.addEventListener('click',()=>playPronunciation(btn)));

const aiButton=document.querySelector('[data-ai-explain]');
if(aiButton){const box=document.querySelector('[data-ai-answer]');aiButton.addEventListener('click',async()=>{aiButton.disabled=true;aiButton.textContent='老師思考中…';try{const r=await fetch('/api/teacher/explain',{method:'POST',headers:{'Accept':'application/json'}});const data=await r.json();box.hidden=false;box.textContent=data.explanation||data.error||'暫時無法產生解說。';}catch(e){box.hidden=false;box.textContent='連線失敗，請稍後再試。';}finally{aiButton.disabled=false;aiButton.textContent='再解釋一次';}})}

const lessonCarousel=document.querySelector('[data-lesson-carousel]');
if(lessonCarousel){
  const cards=[...lessonCarousel.querySelectorAll('[data-lesson-card]')];
  const counter=lessonCarousel.querySelector('[data-lesson-counter]');
  const progress=lessonCarousel.querySelector('[data-lesson-progress]');
  const prev=lessonCarousel.querySelector('[data-lesson-prev]');
  const next=lessonCarousel.querySelector('[data-lesson-next]');
  const start=lessonCarousel.querySelector('[data-lesson-start]');
  let active=0;
  let startX=0;
  const render=()=>{
    cards.forEach((card,index)=>card.classList.toggle('active',index===active));
    if(counter)counter.textContent=`${active+1} / ${cards.length}`;
    if(progress)progress.style.width=`${((active+1)*100/Math.max(cards.length,1)).toFixed(0)}%`;
    if(prev)prev.hidden=active===0;
    if(next)next.hidden=active===cards.length-1;
    if(start)start.hidden=active!==cards.length-1;
  };
  const move=(step)=>{
    active=Math.min(Math.max(active+step,0),cards.length-1);
    render();
  };
  if(prev)prev.addEventListener('click',()=>move(-1));
  if(next)next.addEventListener('click',()=>move(1));
  lessonCarousel.addEventListener('touchstart',event=>{startX=event.touches[0].clientX},{passive:true});
  lessonCarousel.addEventListener('touchend',event=>{
    const delta=event.changedTouches[0].clientX-startX;
    if(Math.abs(delta)>42)move(delta<0?1:-1);
  },{passive:true});
  render();
}

document.querySelectorAll('[data-expand-copy]').forEach(btn=>btn.addEventListener('click',()=>{
  const copy=btn.closest('.lesson-card')?.querySelector('[data-expandable-copy]');
  if(!copy)return;
  const expanded=copy.classList.toggle('expanded');
  btn.textContent=expanded?'收合':'展開';
}));

const navToggle=document.querySelector('[data-nav-toggle]');
const nav=document.querySelector('[data-nav]');
if(navToggle&&nav){navToggle.addEventListener('click',()=>nav.classList.toggle('open'))}
