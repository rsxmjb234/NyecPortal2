"""
Reusable "Create Bug" widget injected into both portal views.

Adds a prominent button in the top bar. Clicking it opens a modal pre-filled
with the current patient's First / Last / DOB and the screen you're on
(e.g. "Marcus - Lab Results"), plus a notes box. On "Go" it shows a
confirmation that, at this point, we would store the ticket as JSON in S3.

Injected by string replacement so it works regardless of the page's f-string
brace escaping. Call inject(html) right before writing the page.
"""

BUG_CSS = """<style>
  .bug-btn { background:#f97316; color:#fff; border:none; font-weight:700; font-size:13.5px;
    padding:9px 16px; border-radius:8px; cursor:pointer; margin-right:14px;
    box-shadow:0 2px 6px rgba(0,0,0,.18); font-family:inherit; white-space:nowrap; }
  .bug-btn:hover { background:#ea580c; }
  .bug-overlay { position:fixed; inset:0; background:rgba(15,23,42,.5); display:none;
    align-items:center; justify-content:center; z-index:9999; }
  .bug-card { background:#fff; width:480px; max-width:92vw; border-radius:14px; overflow:hidden;
    box-shadow:0 20px 60px rgba(0,0,0,.3);
    font-family:system-ui,"Segoe UI",Arial,sans-serif; color:#1f2a37; }
  .bug-head { background:#f97316; color:#fff; font-weight:700; font-size:16px; padding:14px 18px; }
  .bug-body { padding:16px 18px; }
  .bug-row { display:flex; align-items:center; margin-bottom:10px; }
  .bug-row span { width:72px; color:#6b7280; font-size:11px; text-transform:uppercase; letter-spacing:.5px; }
  .bug-row input { flex:1; padding:7px 10px; border:1px solid #e5e9ee; border-radius:7px;
    background:#f1f5f9; color:#1f2a37; font-size:13px; }
  .bug-label { display:block; margin:8px 0 6px; font-weight:600; font-size:13px; }
  .bug-body textarea { width:100%; min-height:92px; padding:9px 11px; border:1px solid #cfd8dc;
    border-radius:8px; font-size:13px; font-family:inherit; resize:vertical; }
  .bug-foot { display:flex; justify-content:flex-end; gap:10px; padding:0 18px 18px; }
  .bug-primary { background:#0ea5a4; color:#fff; border:none; font-weight:700; padding:9px 20px;
    border-radius:8px; cursor:pointer; font-size:13.5px; }
  .bug-primary:hover { background:#0b7c7b; }
  .bug-secondary { background:#eef2f6; color:#475467; border:1px solid #e5e9ee; font-weight:600;
    padding:9px 16px; border-radius:8px; cursor:pointer; font-size:13.5px; }
  .bug-done { padding:4px 18px 20px; }
  .bug-ok { color:#067647; font-weight:700; font-size:15px; margin-bottom:8px; }
  .bug-done p { color:#475467; font-size:12.5px; margin:6px 0; line-height:1.5; }
  .bug-done pre { background:#0f172a; color:#d1fae5; padding:12px; border-radius:8px;
    font-size:12px; overflow:auto; margin:0; }
</style>"""

BUG_BTN = '<button type="button" id="bugBtn" class="bug-btn">&#128030; Create Bug</button>'

BUG_MODAL = """
<div id="bugModal" class="bug-overlay">
  <div class="bug-card">
    <div class="bug-head">Create Bug</div>
    <div class="bug-body" id="bugForm">
      <div class="bug-row"><span>First</span><input id="bugFirst" readonly></div>
      <div class="bug-row"><span>Last</span><input id="bugLast" readonly></div>
      <div class="bug-row"><span>DOB</span><input id="bugDob" readonly></div>
      <div class="bug-row"><span>Screen</span><input id="bugScreen" readonly></div>
      <label class="bug-label">Make Notes</label>
      <textarea id="bugNotes" placeholder="Describe what looks wrong on this screen..."></textarea>
    </div>
    <div class="bug-foot" id="bugFoot">
      <button type="button" class="bug-secondary" id="bugCancel">Cancel</button>
      <button type="button" class="bug-primary" id="bugGo">Go</button>
    </div>
    <div class="bug-done" id="bugDone" style="display:none"></div>
  </div>
</div>
<script>
(function(){
  var modal=document.getElementById('bugModal');
  function g(id){ return document.getElementById(id); }
  function visiblePatient(){
    var all=Array.prototype.slice.call(document.querySelectorAll('.patient'));
    return all.filter(function(p){ return p.style.display!=='none'; })[0] || all[0];
  }
  function screenOf(p){
    var t=p.querySelector('.tab.active'); if(t) return t.textContent.trim();
    var n=p.querySelector('.nav-item.sel'); if(n) return n.textContent.trim();
    var h=p.querySelector('.viewTitle'); if(h) return h.textContent.trim();
    return 'Summary';
  }
  function close(){ modal.style.display='none'; }
  g('bugBtn').addEventListener('click',function(){
    var p=visiblePatient(); if(!p) return;
    g('bugFirst').value=p.getAttribute('data-first')||'';
    g('bugLast').value=p.getAttribute('data-last')||'';
    g('bugDob').value=p.getAttribute('data-dob')||'';
    g('bugScreen').value=(p.getAttribute('data-first')||'')+' - '+screenOf(p);
    g('bugNotes').value='';
    g('bugForm').style.display=''; g('bugFoot').style.display=''; g('bugDone').style.display='none';
    modal.style.display='flex';
  });
  g('bugCancel').addEventListener('click',close);
  modal.addEventListener('click',function(e){ if(e.target===modal) close(); });
  g('bugGo').addEventListener('click',function(){
    var id='BUG-'+String(Date.now()).slice(-6);
    var payload={ticket:id, first:g('bugFirst').value, last:g('bugLast').value,
                 dob:g('bugDob').value, screen:g('bugScreen').value,
                 notes:g('bugNotes').value, createdAt:new Date().toISOString()};
    g('bugForm').style.display='none'; g('bugFoot').style.display='none';
    var d=g('bugDone');
    d.innerHTML='<div class="bug-ok">\u2713 Ticket '+id+' captured</div>'+
      '<p>At this point we would store this as a ticket in S3 '+
      '(s3://nyec-synthetic-data/tickets/'+id+'.json):</p>'+
      '<pre>'+JSON.stringify(payload,null,2).replace(/</g,'&lt;')+'</pre>'+
      '<div class="bug-foot" style="padding:12px 0 0"><button type="button" class="bug-primary" id="bugClose2">Close</button></div>';
    d.style.display='';
    g('bugClose2').addEventListener('click',close);
  });
})();
</script>
"""


def inject(html):
    """Add the Create Bug button + modal to a finished portal page."""
    html = html.replace('</head>', BUG_CSS + '\n</head>', 1)
    html = html.replace('<div class="spacer"></div>',
                        '<div class="spacer"></div>' + BUG_BTN, 1)
    html = html.replace('</body>', BUG_MODAL + '\n</body>', 1)
    return html
