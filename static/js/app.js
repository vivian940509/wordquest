const countdown=document.querySelector('[data-countdown]');
if(countdown){let v=Number(countdown.dataset.countdown||10);const form=document.querySelector('[data-answer-form]');let submitted=false;if(form)form.addEventListener('submit',()=>{submitted=true});const t=setInterval(()=>{v--;countdown.textContent=String(Math.max(v,0));if(v<=5)countdown.classList.add('urgent');if(v<=0){clearInterval(t);if(form&&!submitted){submitted=true;form.querySelectorAll('button').forEach(b=>b.disabled=true);form.requestSubmit();}}},1000)}

const speechButton=document.querySelector('.speech-button');
if(speechButton){const target=speechButton.dataset.speechTarget||'';const speechValue=document.querySelector('#speechValue');const speechScore=document.querySelector('#speechScore');const feedback=document.querySelector('#speechFeedback');const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;speechButton.addEventListener('click',()=>{if(!Recognition){feedback.textContent='此瀏覽器不支援語音辨識，可改用 Chrome。';return}const r=new Recognition();r.lang='en-US';r.interimResults=false;speechButton.classList.add('listening');speechButton.textContent='聽你朗讀中...';r.onresult=e=>{const tr=e.results[0][0].transcript||'';speechValue.value=tr;const a=target.toLowerCase().split(/\s+/),b=tr.toLowerCase().split(/\s+/);let same=0;a.forEach(w=>{if(b.includes(w.replace(/[.,!?]/g,'')))same++});const score=Math.round(100*same/Math.max(a.length,1));speechScore.value=score;feedback.textContent=score>=90?'很接近！節奏和單字都很穩。':score>=75?'很接近，再慢一點會更清楚。':score>=55?'有抓到大部分內容，試著每個字分開唸。':'再慢一點，注意 th、r、v 等音。';speechButton.textContent=`辨識到：${tr}`;speechButton.classList.remove('listening')};r.onerror=()=>{feedback.textContent='辨識失敗，請再試一次。';speechButton.classList.remove('listening')};r.start()})}

let activePronunciationAudio=null;
let activeSpeechUtterance=null;
const pronunciationFailures=new Map();

const waitForVoices=()=>new Promise(resolve=>{
  if(!('speechSynthesis' in window)){resolve([]);return}
  const existing=window.speechSynthesis.getVoices();
  if(existing.length){resolve(existing);return}
  let done=false;
  const finish=()=>{if(done)return;done=true;resolve(window.speechSynthesis.getVoices())};
  window.speechSynthesis.addEventListener?.('voiceschanged',finish,{once:true});
  setTimeout(finish,700);
});

const stopPronunciation=()=>{
  if(activePronunciationAudio){
    try{activePronunciationAudio.pause();activePronunciationAudio.currentTime=0}catch(e){}
    activePronunciationAudio=null;
  }
  if('speechSynthesis' in window){
    try{window.speechSynthesis.cancel()}catch(e){}
  }
  activeSpeechUtterance=null;
};

const speakWithBrowser=async(word)=>{
  if(!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance)throw new Error('tts unavailable');
  const voices=await waitForVoices();
  return new Promise((resolve,reject)=>{
    try{
      window.speechSynthesis.cancel();
      const u=new SpeechSynthesisUtterance(word);
      const voice=voices.find(v=>/^en-US/i.test(v.lang))||voices.find(v=>/^en-GB/i.test(v.lang))||voices.find(v=>/^en/i.test(v.lang));
      if(voice)u.voice=voice;
      u.lang=voice?.lang||'en-US';u.rate=.82;u.pitch=1;u.volume=1;
      let settled=false;
      const finish=(ok)=>{if(settled)return;settled=true;activeSpeechUtterance=null;ok?resolve():reject(new Error('tts failed'))};
      u.onend=()=>finish(true);u.onerror=()=>finish(false);
      activeSpeechUtterance=u;
      // Some Android WebViews report speechSynthesis as paused after navigation.
      window.speechSynthesis.resume();
      window.speechSynthesis.speak(u);
      setTimeout(()=>{if(!settled&&!window.speechSynthesis.speaking)finish(false)},1200);
      setTimeout(()=>finish(true),Math.max(3500,word.length*350));
    }catch(e){reject(e)}
  });
};

const playSameOriginAudio=(word)=>new Promise((resolve,reject)=>{
  const url=`/api/pronounce/audio?word=${encodeURIComponent(word)}`;
  const audio=new Audio();
  activePronunciationAudio=audio;
  audio.preload='auto';audio.volume=1;audio.playsInline=true;
  let settled=false;
  const cleanup=()=>{audio.onended=null;audio.onerror=null;audio.oncanplay=null};
  const finish=(ok,err)=>{if(settled)return;settled=true;cleanup();if(activePronunciationAudio===audio)activePronunciationAudio=null;ok?resolve():reject(err||new Error('audio failed'))};
  audio.onended=()=>finish(true);
  audio.onerror=()=>finish(false,new Error('audio network/decoder failed'));
  // Assign src and call play synchronously from the user's tap call stack.
  audio.src=url;
  const playPromise=audio.play();
  if(playPromise?.catch)playPromise.catch(err=>finish(false,err));
  setTimeout(()=>{if(!settled&&audio.paused&&audio.readyState<2)finish(false,new Error('audio timeout'))},7000);
});

const playPronunciation=async(btn)=>{
  const word=(btn.dataset.speakWord||'').trim();
  if(!word)return;
  stopPronunciation();
  const original=btn.dataset.originalLabel||btn.textContent;
  btn.dataset.originalLabel=original;
  btn.disabled=true;btn.classList.add('speaking');btn.textContent='載入發音…';
  let played=false;
  try{
    await playSameOriginAudio(word);
    played=true;
    pronunciationFailures.delete(word.toLowerCase());
  }catch(e){
    const key=word.toLowerCase();pronunciationFailures.set(key,(pronunciationFailures.get(key)||0)+1);
  }
  if(!played){
    btn.textContent='切換手機語音…';
    try{await speakWithBrowser(word);played=true}catch(e){}
  }
  btn.disabled=false;btn.classList.remove('speaking');btn.textContent=played?original:'暫時無法播放，請再試一次';
  if(!played)setTimeout(()=>{btn.textContent=original},2200);
};

document.querySelectorAll('[data-speak-word]').forEach(btn=>{
  // click/touch is deliberately bound directly to preserve mobile user gesture.
  btn.addEventListener('click',()=>playPronunciation(btn));
});

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
