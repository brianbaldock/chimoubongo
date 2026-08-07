(function(){
  var els=Array.prototype.slice.call(document.querySelectorAll('.rv'));
  if(!els.length) return;
  var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion:reduce)').matches;
  function showAll(){els.forEach(function(e){e.classList.add('in')});}
  if(!('IntersectionObserver' in window)||reduce){showAll();return;}

  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(x){
      if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target);}
    });
  },{rootMargin:'200px 0px 0px 0px',threshold:0});

  els.forEach(function(e){
    // anything already on screen (or just above it) reveals immediately, no scroll needed
    var r=e.getBoundingClientRect();
    if(r.top < (window.innerHeight||0) + 200){ e.classList.add('in'); }
    else { io.observe(e); }
  });

  // failsafe: content must never stay hidden
  setTimeout(function(){
    els.forEach(function(e){
      var r=e.getBoundingClientRect();
      if(r.top < (window.innerHeight||0)*1.5) e.classList.add('in');
    });
  },1200);
  window.addEventListener('load',function(){
    els.forEach(function(e){
      var r=e.getBoundingClientRect();
      if(r.top < (window.innerHeight||0)+200) e.classList.add('in');
    });
  });
})();
