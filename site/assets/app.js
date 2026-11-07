// EdgeTokens: theme, menu, reveal, sort/filter tables, value tabs, board picker. Vanilla, no deps.
(function(){
var d=document,R=d.documentElement,$=function(s,c){return(c||d).querySelector(s)},$$=function(s,c){return Array.prototype.slice.call((c||d).querySelectorAll(s))};
R.classList.add('js');
// theme toggle (dark is the default; the choice is remembered)
var tb=$('#theme');if(tb)tb.onclick=function(){var nx=(R.dataset.theme||'dark')==='dark'?'light':'dark';R.dataset.theme=nx;try{localStorage.setItem('et-theme',nx)}catch(e){}};
// mobile menu
var top=$('#top'),mb=$('#menu');if(mb&&top){var setM=function(o){top.classList.toggle('open',o);mb.setAttribute('aria-expanded',o);d.body.style.overflow=o?'hidden':''};
  mb.onclick=function(){setM(!top.classList.contains('open'))};
  $$('#nav a').forEach(function(a){a.addEventListener('click',function(){setM(false)})});
  d.addEventListener('keydown',function(e){if(e.key==='Escape'&&top.classList.contains('open')){setM(false);mb.focus()}})}
// scroll reveal
var rv=$$('.reveal');if(R.classList.contains('io')){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px',threshold:0});
  rv.forEach(function(el){io.observe(el)})}else rv.forEach(function(el){el.classList.add('in')});
// sortable tables
$$('table.lb').forEach(function(t){$$('th',t).forEach(function(th,i){function go(){
  var asc=!th.classList.contains('asc');$$('th',t).forEach(function(x){x.classList.remove('asc','desc');x.setAttribute('aria-sort','none')});
  th.classList.add(asc?'asc':'desc');th.setAttribute('aria-sort',asc?'ascending':'descending');var num=th.dataset.type==='num',b=t.tBodies[0];
  Array.prototype.slice.call(b.rows).sort(function(x,y){var a=x.cells[i],c=y.cells[i],va=num?parseFloat(a.dataset.v||a.textContent):a.textContent.toLowerCase(),vb=num?parseFloat(c.dataset.v||c.textContent):c.textContent.toLowerCase();
  return(va>vb?1:va<vb?-1:0)*(asc?1:-1)}).forEach(function(r){b.appendChild(r)});t.dispatchEvent(new Event('sorted'))}
  th.addEventListener('click',go);th.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();go()}})})});
// leaderboard filters (+ show the top 25 until expanded or filtered)
var q=$('#q');if(q){var t=$('table.lb'),cnt=$('#count'),fb=$('#f-board'),fs=$('#f-size'),fr=$('#f-rt'),more=$('#showall'),LIM=25,all=false,tot=t.tBodies[0].rows.length;
  var apply=function(){var w=q.value.toLowerCase().split(/\s+/).filter(Boolean),n=0,filtered=!!(w.length||fb.value||fs.value||fr.value);
    Array.prototype.slice.call(t.tBodies[0].rows).forEach(function(r){var x=r.textContent.toLowerCase();
    var ok=w.every(function(s){return x.indexOf(s)>=0})&&(!fb.value||r.dataset.board===fb.value)&&(!fs.value||r.dataset.size===fs.value)&&(!fr.value||r.dataset.rt===fr.value);
    if(ok)n++;r.hidden=!ok||(!all&&!filtered&&n>LIM)});
    cnt.textContent=n===tot?tot+' runs':n+' of '+tot+' runs';
    if(more){more.hidden=all||filtered||n<=LIM;more.textContent='Show all '+n+' runs'}
    var u=new URLSearchParams();if(q.value)u.set('q',q.value);if(fb.value)u.set('board',fb.value);if(fs.value)u.set('size',fs.value);if(fr.value)u.set('rt',fr.value);
    history.replaceState(null,'',location.pathname+(u.toString()?'?'+u:'')+location.hash)};
  var p=new URLSearchParams(location.search);q.value=p.get('q')||'';fb.value=p.get('board')||'';fs.value=p.get('size')||'';fr.value=p.get('rt')||'';
  q.addEventListener('input',apply);[fb,fs,fr].forEach(function(s){s.addEventListener('change',apply)});t.addEventListener('sorted',apply);
  if(more)more.onclick=function(){all=true;apply()};
  $('#clear').onclick=function(){q.value=fb.value=fs.value=fr.value='';apply()};apply();t.classList.add('ready')}
// value tabs (segmented control, arrow keys move between tabs)
var tabs=$$('[data-tab]');if(tabs.length){var show=function(id){tabs.forEach(function(b){var on=b.dataset.tab===id;b.setAttribute('aria-selected',on);b.tabIndex=on?0:-1;var p=d.getElementById(b.dataset.tab);if(p)p.hidden=!on})};
  tabs.forEach(function(b,i){b.onclick=function(){show(b.dataset.tab);history.replaceState(null,'','#'+b.dataset.tab)};
    b.onkeydown=function(e){var k=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;if(!k)return;e.preventDefault();var n=tabs[(i+k+tabs.length)%tabs.length];n.focus();n.click()}});
  var h=location.hash.slice(1);show(h&&d.getElementById(h)?h:tabs[0].dataset.tab)}
// board picker
var pd=$('#pick-data');if(pd){var D=JSON.parse(pd.textContent),out=$('#pk-out'),st={budget:200,size:'mid'};
  var el=function(tag,cls,txt){var e=d.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e};
  var link=function(href,txt,cls,rel){var a=el('a',cls,txt);a.href=href;a.target='_blank';a.rel=rel||'nofollow noopener';return a};
  var money=function(v){return '$'+(v%1?v.toFixed(2):v.toLocaleString('en-US'))};
  var verdict=function(v){return v>=10?['yes','Chat speed']:v>=4?['ok','Usable']:['slow','Slow']};
  var render=function(){var best={};D.forEach(function(r){if(r.s!==st.size)return;if(st.budget&&r.price>st.budget)return;if(!best[r.p]||r.t>best[r.p].t)best[r.p]=r});
    var L=Object.keys(best).map(function(k){return best[k]}).sort(function(a,b){return b.t-a.t||a.price-b.price});out.textContent='';
    if(!L.length){var e=el('div','callout');e.appendChild(el('b',null,'No sourced runs in this budget and size yet. '));e.appendChild(d.createTextNode('Try a bigger budget or a smaller model, or '));var s=link('../submit/index.html','submit a run');s.removeAttribute('target');e.appendChild(s);e.appendChild(d.createTextNode(' if you have one.'));out.appendChild(e);return}
    out.appendChild(el('p','pk-meta',L.length+' board'+(L.length>1?'s':'')+' match. Showing the top '+Math.min(5,L.length)+', fastest measured first.'));
    var wrap=el('div','recs swap');L.slice(0,5).forEach(function(r,i){var c=el('article','rec'+(i?'':' top')),v=verdict(r.t);
      if(!i){var g=el('div','glow');g.setAttribute('aria-hidden','true');c.appendChild(g)}
      var mid=el('div');mid.appendChild(el('div','rk',i?'#'+(i+1):'Top pick'));var h=el('h3'),a=el('a',null,r.b);a.href='../boards/'+r.p+'/index.html';h.appendChild(a);mid.appendChild(h);
      var vd=el('div','vd '+v[0]);vd.appendChild(el('i'));vd.appendChild(d.createTextNode(v[1]));mid.appendChild(vd);
      var m=el('div','sub');m.appendChild(d.createTextNode(r.m+' · '+r.rt+' · '+r.q+' · '));m.appendChild(link(r.src,'source ↗','src'));mid.appendChild(m);c.appendChild(mid);
      var sp=el('div','spd'),sn=el('span',i?null:'grad',String(r.t));sp.appendChild(sn);sp.appendChild(el('small',null,'tok/s · '+money(r.price)));c.appendChild(sp);
      var bd=el('div','bd');bd.appendChild(el('div','sub',r.hw+'. '+r.basis));var by=el('div','buy');r.buy.forEach(function(x){var sd=/seeedstudio/.test(x.u),b=link(x.u,x.l,'aff'+(sd?' seeed':''),'sponsored nofollow noopener');b.setAttribute('data-aff-slot',sd?'seeed-'+r.p:r.p);by.appendChild(b)});bd.appendChild(by);c.appendChild(bd);wrap.appendChild(c)});
    out.appendChild(wrap)};
  var seg=function(id,key,parse){$$('#'+id+' .seg').forEach(function(b){b.onclick=function(){$$('#'+id+' .seg').forEach(function(x){x.setAttribute('aria-pressed',x===b)});st[key]=parse(b.dataset[key]);render()}})};
  seg('pk-budget','budget',function(v){return +v});seg('pk-size','size',function(v){return v});render()}
// submit form prefill
var f=$('#submit-form');if(f){var sp=new URLSearchParams(location.search);if(sp.get('board'))f.board.value=sp.get('board');if(sp.get('model'))f.model.value=sp.get('model')}
})();
