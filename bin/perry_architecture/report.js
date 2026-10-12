'use strict';
const data = JSON.parse(document.getElementById('data').textContent);
const $ = id => document.getElementById(id);
const files = new Map(data.files.map(f => [f.id, f]));
let scope = '', selected = null, pairs = [], boundary = false, mode = data.architecture ? 'architecture' : 'files';
const architecture = data.architecture;
const semantic = architecture?.version === 2;
const evidenceItem = id => typeof id==='number'?data.imports[id]:data.evidence?.[id];
const components = new Map((architecture?.nodes || []).map(n => [n.id,n]));
const pathInside = (path, dir) => !dir || path.startsWith(dir + '/');
function inside(path, dir) {
  if(mode === 'files') return pathInside(path,dir);
  if(semantic && files.has(path) && dir) return components.get(dir)?.files.includes(path) || false;
  const owner = components.has(path)?path:(architecture.owners[path] || path);
  return owner === dir || pathInside(owner,dir);
}
function nameOf(path) { return mode==='architecture' ? components.get(path)?.label || path : path; }
function shownEdges() { return mode==='architecture' ? architecture.edges : data.edges; }
const short = path => path.split('/').pop();
function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
function button(text, action, cls) {
  const node = el('button', text, cls); node.onclick = action; return node;
}
function label(text) { return el('div', text, 'panel-label'); }
function state(next) { location.hash = encodeURIComponent(JSON.stringify({mode,boundary,...next})); }
function showScope(path) { state({scope: path}); }
function members(path) { return files.has(path) ? [files.get(path)] : semantic&&mode==='architecture'&&path?(components.get(path)?.files||[]).map(id=>files.get(id)):data.files.filter(f => inside(f.id, path)); }
function localNodes(){return semantic&&mode==='architecture'?[...components.values()].filter(n=>n.parent===scope&&n.files.length).map(n=>n.id).concat(scope&&![...components.values()].some(n=>n.parent===scope)?[scope]:[]):data.files.filter(f=>inside(f.id,scope)).map(f=>project(f.id));}
function project(path) {
  if(mode==='architecture') {
    const owner=components.has(path)?path:architecture.owners[path];
    if(owner===scope)return scope;
    if(pathInside(owner,scope))return (scope?scope+'/':'')+(scope?owner.slice(scope.length+1):owner).split('/')[0];
    const own=scope.split('/'), parts=owner.split('/');
    let i=0;while(i<own.length&&own[i]===parts[i])i++;
    return parts.slice(0,i+1).join('/');
  }
  if (inside(path, scope)) {
    const remainder = scope ? path.slice(scope.length + 1) : path;
    return (scope ? scope + '/' : '') + remainder.split('/')[0];
  }
  // Keep boundary neighbours visible at the nearest sibling of this scope.
  const own = scope.split('/'), parts = path.split('/');
  let i = 0; while (i < own.length && own[i] === parts[i]) i++;
  return parts.slice(0, i + 1).join('/');
}
function navigation() {
  const q = $('search').value.toLowerCase().trim(), tree = $('tree'); tree.replaceChildren();
  tree.append(button('◈  项目总览', () => showScope(''), 'tree-row' + (!scope ? ' active' : '')));
  if (q) {
    const matches = data.files.filter(f => f.id.toLowerCase().includes(q));
    if(mode==='architecture')for(const component of components.values()){
      if((component.label+component.description).toLowerCase().includes(q))tree.append(button(component.label,()=>showScope(component.id),'tree-row'));
    }
    matches.slice(0, 100).forEach(f => tree.append(button(f.id, () => state({scope: mode==='architecture'?architecture.owners[f.id]:(f.id.includes('/') ? f.id.slice(0,f.id.lastIndexOf('/')) : ''), file:f.id}), 'tree-row')));
    tree.append(el('p', `${matches.length} 个匹配${matches.length > 100 ? '，显示前 100 个' : ''}`, 'hint')); return;
  }
  if(mode==='architecture') {
    for(const component of components.values()) {
      if(component.parent && component.parent!==scope && !scope.startsWith(component.parent+'/'))continue;
      const b=button(component.label,()=>showScope(component.id),'tree-row'+(scope===component.id?' active':''));
      b.style.paddingLeft=7+(component.id.split('/').length-1)*13+'px';
      b.title=component.description;b.append(el('small',component.files.length));tree.append(b);
    }
    return;
  }
  const dirs = new Set();
  for (const f of data.files) {
    const parts = f.id.split('/');
    for (let i=1; i<parts.length; i++) dirs.add(parts.slice(0,i).join('/'));
  }
  [...dirs].sort().filter(d => !d.includes('/') || scope === d || scope.startsWith(d.slice(0,d.lastIndexOf('/')) + '/') || scope === d.slice(0,d.lastIndexOf('/'))).forEach(d => {
    const b = button('▧  ' + short(d), () => showScope(d), 'tree-row' + (scope === d ? ' active' : ''));
    b.style.paddingLeft = 7 + (d.split('/').length - 1)*13 + 'px'; b.title = d;
    b.append(el('small', members(d).length)); tree.append(b);
  });
}
function buildGraph() {
  const ids = new Set(localNodes());
  const aggregate = new Map();
  for (const edge of shownEdges()) {
    if (!inside(edge.source, scope) && !inside(edge.target, scope)) continue;
    const a = project(edge.source), b = project(edge.target);
    if (a === b) continue;
    if(mode==='files'||boundary||inside(a,scope))ids.add(a);
    if(mode==='files'||boundary||inside(b,scope))ids.add(b);
    const key = JSON.stringify([a,b]);
    if (!aggregate.has(key)) aggregate.set(key, {a,b,edges:[],ids:new Set()});
    const pair = aggregate.get(key); pair.edges.push(edge); edge.imports.forEach(id => pair.ids.add(id));
  }
  pairs = [...aggregate.values()].sort((a,b) => a.a.localeCompare(b.a) || a.b.localeCompare(b.b));
  const graph = $('graph'); graph.replaceChildren();
  const all = [...ids].sort((a,b) => Number(!inside(a,scope))-Number(!inside(b,scope)) || a.localeCompare(b));
  const visible = all.slice(0,80), positions = new Map();
  if (all.length > 80) graph.append(el('p','此层超过 80 个节点，图显示前 80 个；依赖列表保留全部关系。请从左侧下钻。','notice'));
  if (!visible.length) { graph.append(el('div','没有可显示的 Python 文件。查看扫描范围与限制。','empty')); return; }
  const ns='http://www.w3.org/2000/svg';
  function svg(tag, attrs, text) { const n=document.createElementNS(ns,tag); for(const [k,v] of Object.entries(attrs||{})) n.setAttribute(k,v); if(text!==undefined)n.textContent=text; return n; }
  let columns=visible.length<=6?2:3, width=columns*220+50, height=Math.ceil(visible.length/columns)*108+45;
  const rows=new Map();
  if(mode==='architecture') {
    const maxLayer=Math.max(0,...visible.filter(id=>inside(id,scope)).map(id=>components.get(id).layer));
    for(const id of visible){
      const layer=scope&&!inside(id,scope)?maxLayer+1:components.get(id).layer;
      if(!rows.has(layer))rows.set(layer,[]);rows.get(layer).push(id);
    }
    columns=Math.max(2,...[...rows.values()].map(row=>row.length));
    width=columns*250+50;height=rows.size*120+35;
  }
  const canvas=svg('svg',{viewBox:`0 0 ${width} ${height}`,role:'group','aria-label':'模块依赖：点击节点下钻，点击连线查看证据'});
  const defs=svg('defs'), marker=svg('marker',{id:'arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});
  marker.append(svg('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#8aa797'}));defs.append(marker);canvas.append(defs);
  if(mode==='architecture') {
    [...rows].sort((a,b)=>a[0]-b[0]).forEach(([layer,ids],r)=>ids.forEach((id,c)=>
      positions.set(id,{x:(width-ids.length*250)/2+c*250+15,y:28+r*120})));
  } else visible.forEach((id,i)=>positions.set(id,{x:25+(i%columns)*220,y:25+Math.floor(i/columns)*108}));
  for (const pair of pairs) {
    if(!positions.has(pair.a)||!positions.has(pair.b))continue;
    const a=positions.get(pair.a),b=positions.get(pair.b);
    // Route through row gutters, never through unrelated module cards.
    const forward=pair.a<pair.b, offset=forward?12:20;
    const x1=a.x+(forward?80:110), x2=b.x+(forward?80:110);
    const gutter=forward?8:width-8;
    let d=a.y===b.y
      ? `M${x1},${a.y} V${a.y-offset} H${x2} V${b.y}`
      : `M${x1},${a.y} V${a.y-offset} H${gutter} V${b.y-offset} H${x2} V${b.y}`;
    const adjacent=mode==='architecture'&&b.y-a.y===120;
    if(adjacent)d=`M${a.x+110},${a.y+80} C${a.x+110},${a.y+100} ${b.x+110},${b.y-20} ${b.x+110},${b.y}`;
    if(mode==='architecture'&&a.y===b.y)d=a.x<b.x?`M${a.x+220},${a.y+40} H${b.x}`:`M${a.x},${a.y+40} H${b.x+220}`;
    const crossLayer=mode==='architecture'&&!adjacent&&a.y!==b.y;
    const group=svg('g',{class:'edge-group'+(crossLayer?' cross-layer':'')+(selected?.a===pair.a&&selected?.b===pair.b?' active':''),
      role:'button',tabindex:0,'aria-label':`${nameOf(pair.a)} → ${nameOf(pair.b)}`});
    group.append(svg('title',{},`${nameOf(pair.a)} → ${nameOf(pair.b)} · ${pair.ids.size} 条源码证据`));
    group.append(svg('path',{d,class:'graph-edge','marker-end':'url(#arrow)'}),svg('path',{d,class:'graph-hit'}));
    group.onclick=()=>state({scope,edge:[pair.a,pair.b]});
    group.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();group.onclick();}};
    canvas.append(group);
  }
  for(const id of visible){
    const pos=positions.get(id),file=files.has(id),outside=scope&&!inside(id,scope),count=members(id).length;
    const isArchitecture=mode==='architecture', component=components.get(id);
    const group=svg('g',{class:'graph-node'+(file?' file':'')+(outside?' outside':'')+(isArchitecture?' responsibility':''),role:'button',tabindex:0,'aria-label':nameOf(id)});
    group.append(svg('title',{},isArchitecture?component.description:id),svg('rect',{x:pos.x,y:pos.y,width:isArchitecture?220:190,height:isArchitecture?80:62,rx:9}));
    const name=isArchitecture?component.label:short(id);group.append(svg('text',{x:pos.x+12,y:pos.y+25},name.length>24?name.slice(0,22)+'…':name));
    if(isArchitecture)group.append(svg('text',{x:pos.x+12,y:pos.y+47,class:'node-sub'},component.description.slice(0,21)));
    group.append(svg('text',{x:pos.x+12,y:pos.y+(isArchitecture?70:46),class:'node-sub'},file?`${files.get(id).lines.toLocaleString()} 行 · 查看源码 ↗`:`${count} 个实现文件 · ${outside?'范围外组件':'展开'} →`));
    const action=()=>file?state({scope,file:id}):showScope(id);group.onclick=action;group.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();action();}};canvas.append(group);
  }
  graph.append(canvas);
  graph.append(el('p',mode==='architecture'?'职责分层由分析模型提供，连线由静态引用聚合；浅色线表示跨层引用。范围外关系始终列在下方，可勾选后加入图中。':'目录节点按真实路径聚合；同一节点内部的依赖在下钻后显示。虚线节点是当前范围之外的依赖方。','hint'));
}
function relations() {
  const box=$('relations');box.replaceChildren();
  for(const pair of pairs){
    const row=button('',()=>state({scope,edge:[pair.a,pair.b]}),'relation'+(selected===pair?' active':''));
    row.append(el('span',nameOf(pair.a)),el('span','→','arrow'),el('span',nameOf(pair.b)),el('span',`${pair.edges.length} 对关系 · ${pair.ids.size} 处`,'count'));box.append(row);
  }
  if(!pairs.length)box.append(el('div','此层没有跨节点的已解析依赖。文件内部、自依赖和未解析项可在文件详情中查看。','empty'));
}
function metrics(items) {
  const grid=el('div',undefined,'metric-grid');for(const [value,name] of items){const cell=el('div');cell.append(el('b',value),el('span',name));grid.append(cell);}return grid;
}
function scopeDetails() {
  const box=$('details');box.replaceChildren(label(mode==='architecture'?'RESPONSIBILITY / IMPLEMENTATION':'MODULE / OVERVIEW'),el('h2',nameOf(scope)||data.project,'panel-title'));
  const fs=members(scope),set=new Set(fs.map(f=>f.id));
  const contains=path=>semantic&&mode==='architecture'?inside(path,scope):set.has(path);
  box.append(el('p',mode==='architecture'?(components.get(scope)?.description||architecture.basis):'这里显示代码的实际组织方式。目录名称与 import 关系不代表经过确认的业务职责。','muted'));
  box.append(metrics([[fs.length,'Python 文件'],[fs.reduce((s,f)=>s+f.lines,0).toLocaleString(),'源码行数'],[shownEdges().filter(e=>!set.has(e.source)&&set.has(e.target)).length,'范围外依赖此处'],[shownEdges().filter(e=>contains(e.source)&&!contains(e.target)).length,'此处依赖范围外']]));
  if(mode==='architecture'){
    if(semantic&&scope){
      const component=components.get(scope);
      box.append(el('p','判断边界：'+component.uncertainty,'notice'));
      const justification=el('details');justification.append(el('summary','职责判断的源码依据'));evidenceList(component.evidence,justification);box.append(justification);
      if(component.symbols.length){const list=el('details');list.append(el('summary',`符号成员 (${component.symbols.length})`));evidenceList(component.symbols,list);box.append(list);}
    }
    const implementation=el('details');implementation.open=scope&&!architecture.nodes.some(n=>n.parent===scope);
    implementation.append(el('summary',`实现文件 (${fs.length})`));
    for(const f of fs)implementation.append(button(f.id,()=>state({scope,file:f.id}),'tree-row'));
    box.append(implementation);
    box.append(el('p','这一层只展示职责组件。进入组件看子架构；实现文件与连线中的 import 记录用于核查。','muted'));
  }else box.append(el('h2','从结构到证据'),el('p','点击目录节点进入下一层；点击文件查看 import 列表；点击依赖连线或下方关系，定位形成这条依赖的源码。','muted'));
  box.append(el('div','这是一次代码快照。修改代码后重新扫描，报告不会自动刷新。','notice'));
}
function evidenceList(ids, box) {
  for(const id of [...ids].sort((a,b)=>evidenceItem(a).source.localeCompare(evidenceItem(b).source)||evidenceItem(a).line-evidenceItem(b).line)){
    const item=evidenceItem(id), b=button(`${item.source}:${item.line} · ${item.kind||'import'}`,()=>state({scope,...(selected?{edge:[selected.a,selected.b]}:{}),import:id}),'evidence');
    if(item.symbol)b.append(el('small',`符号: ${item.symbol}`));
    b.append(el('code',item.statement));
    if(item.targets?.length)b.append(el('small','→ '+item.targets.join(', ')));
    if(item.canonical)b.append(el('small','→ '+item.canonical));
    box.append(b);
  }
}
function edgeDetails(pair, itemId) {
  const box=$('details');box.replaceChildren(label('DEPENDENCY / EVIDENCE'),el('h2',`${nameOf(pair.a)} → ${nameOf(pair.b)}`,'panel-title'));
  box.append(el('p',`${pair.edges.length} 对静态关系，由 ${pair.ids.size} 条源码记录产生。${mode==='architecture'?'只展示显式引用；不宣称运行时调用或读写流程。':'包含明确可解析的包初始化依赖。'}`,'muted'));
  const list=el('details');list.open=itemId===undefined;list.append(el('summary',`源码证据 (${pair.ids.size})`));evidenceList(pair.ids,list);box.append(list);
  if(itemId!==undefined)source(evidenceItem(itemId).source,evidenceItem(itemId).line,evidenceItem(itemId).end_line);
}
function fileDetails(path, line=1) {
  const f=files.get(path);if(!f)return scopeDetails();
  const box=$('details');box.replaceChildren(label('FILE / SOURCE'),el('h2',path,'panel-title'));
  box.append(el('p',`${f.kind} · ${f.lines} 行 · ${f.status}`,'muted'));
  const outgoing=data.imports.filter(i=>i.source===path),incoming=new Set(data.edges.filter(e=>e.target===path).flatMap(e=>e.imports));
  for(const [title,ids] of [['此文件的 imports',outgoing.map(i=>i.id)],['被哪些源码依赖',[...incoming]]]){
    const list=el('details');list.append(el('summary',`${title} (${ids.length})`));evidenceList(ids,list);box.append(list);
  }
  if(data.calls){const list=el('details');const ids=data.calls.filter(c=>c.source===path).map(c=>c.id);list.append(el('summary',`调用表达式 (${ids.length})`));evidenceList(ids,list);box.append(list);}
  source(path,line,line);
}
function source(path,line,end) {
  const box=$('details'),f=files.get(path);if(!f)return;
  box.append(el('p',`${path}:${line}${end!==line?'-'+end:''}`,'hint'));
  const header=el('div',undefined,'source-head'),input=el('input');input.type='number';input.min=1;input.max=Math.max(1,f.lines);input.value=line;input.setAttribute('aria-label','跳转到源码行');
  header.append(el('span','行号'),input,button('跳转',()=>state({scope,file:path,line:Math.max(1,Math.min(f.lines,Number(input.value)||1))})));box.append(header);
  const pre=el('div',undefined,'source'),lines=f.source.split(/\r?\n/),start=Math.max(1,line-8),stop=Math.min(lines.length,Math.max(line+18,end+3));
  for(let n=start;n<=stop;n++){const row=el('div',undefined,'code-line'+(n>=line&&n<=end?' highlight':''));row.append(el('span',n,'line-no'),el('span',lines[n-1]));pre.append(row);}box.append(pre);
  box.append(el('p',`显示 ${start}–${stop} 行 / 共 ${f.lines} 行 · 来源是扫描时的源码快照`,'hint'));
}
function coverage() {
  const box=$('details');box.replaceChildren(label('COVERAGE / LIMITS'),el('h2','扫描范围与限制','panel-title'));
  if(architecture){
    box.append(el('p',architecture.basis,'notice'));
    box.append(el('p',`架构映射问题：${architecture.issues.length} 项；分组模型 ${architecture.model_sha256.slice(0,12)}`,'muted'));
    for(const issue of architecture.issues)box.append(el('p',`${issue.kind}: ${issue.path} ${issue.candidates.join(', ')}`,'issue'));
  }
  box.append(el('p',`解析成功 ${data.summary.parsed} / ${data.summary.files} 个候选文件。只分析 Python AST，不执行项目代码。`,'muted'));
  box.append(el('div','未解析不等于外部依赖：它也可能是被排除的文件、未配置的导入根或动态加载。函数内与条件内 import 都保留，不代表运行时一定执行。','notice'));
  box.append(el('pre',`根目录: ${data.root}\n导入根: ${data.scope.source_roots.join(', ')}\n排除: ${data.scope.excludes.join(', ')||'无自定义'}\n文件上限: ${data.scope.max_file_bytes} bytes\nPython: ${data.python}`,'scope-list'));
  box.append(el('p','默认排除目录：'+data.scope.default_excluded_dirs.join(', '),'muted'));
  box.append(el('p','调用仅作保守的词法解析，不覆盖完整运行时调用图、反射、文件/数据库读写、非 Python 代码。未模拟 sys.path 优先级；同名候选标记为 ambiguous。','muted'));
  const skipped=el('details');skipped.append(el('summary',`跳过的路径 (${data.scope.skipped_paths.length})`),el('pre',data.scope.skipped_paths.join('\n'),'scope-list'));box.append(skipped);
  const unresolved=data.imports.filter(i=>['unresolved','ambiguous'].includes(i.resolution));
  const list=el('details');list.append(el('summary',`未解析 / 歧义 import (${unresolved.length})`));evidenceList(unresolved.map(i=>i.id),list);box.append(list);
  for(const issue of data.issues){const item=el('div',undefined,'issue');item.append(el('strong',`${issue.kind} · ${issue.path}:${issue.line}`),el('p',issue.message));if(files.has(issue.path))item.append(button('查看源码',()=>state({scope,file:issue.path,line:issue.line||1})));box.append(item);}
}
function comparison(){
  const box=$('details');box.replaceChildren(label('TARGET / CURRENT / EVIDENCE'),el('h2','目标对比','panel-title'));
  if(data.comparison){
    box.append(el('p','目标来自用户架构文档；检查规则由 agent 解释提取。原文与版本已校验，规则解释仍需审阅。','notice'));
    const statuses={violation:'发现偏离',unknown:'无法完整判断',no_observed_violation:'未观察到违反'};
    for(const rule of data.comparison.results){
      box.append(el('h3',rule.id+' · '+statuses[rule.status]),el('p','本次只检查 '+rule.kind+': '+(rule.constraint||[]).join(', '),'muted'),el('p',`${rule.source.path}:${rule.source.line} · 检查 ${rule.checked_files} 个文件`,'hint'),el('pre',rule.source.quote,'scope-list'));
      for(const finding of rule.violations){box.append(el('p',finding.reason,'issue'));evidenceList(finding.evidence,box);}
      if(rule.unknown.length){const unknown=el('details');unknown.append(el('summary',`无法判断 (${rule.unknown.length})`));for(const finding of rule.unknown){unknown.append(el('p',finding.reason,'muted'));evidenceList(finding.evidence,unknown);}box.append(unknown);}
    }
    box.append(el('p','只检查已列出的规则与扫描范围，不代表整个架构合规。修实现或改目标的决定沿用 Perry 现有审计流程。','notice'));
  }else box.append(el('p','未提供目标规则；当前只有代码现状，不做合规判断。'));
  if(data.changes){box.append(el('h3','与上次快照相比'));for(const key of ['added','removed','changed','components_added','components_removed','components_changed'])box.append(el('p',key+': '+(data.changes[key].join(', ')||'无'),'hint'));}
}
function render() {
  let view={};try{view=JSON.parse(decodeURIComponent(location.hash.slice(1))||'{}');}catch{}
  if(!view || typeof view!=='object' || Array.isArray(view))view={};
  mode=architecture&&view.mode!=='files'?'architecture':'files';
  boundary=view.boundary===true;
  $('boundary').checked=boundary;
  $('boundary').disabled=mode==='files';
  const requested=mode==='architecture'?(architecture.scope_aliases[view.scope]||view.scope):view.scope;
  scope=typeof requested==='string'&&(!requested||(mode==='architecture'?components.has(requested):data.files.some(f=>inside(f.id,requested))))?requested:'';
  $('architecture-view').disabled=!architecture;
  $('architecture-view').classList.toggle('active',mode==='architecture');
  $('file-view').classList.toggle('active',mode==='files');
  $('view-note').textContent=mode==='architecture'?'职责分层 → 子架构 → 源码证据':'目录与文件级依赖，不等同于架构';
  $('diagram-title').textContent=mode==='architecture'?'职责组件与静态引用':'目录与文件依赖';
  $('legend').textContent=mode==='architecture'?'节点是职责组件 · 箭头指向被引用方':'节点是目录或文件 · 箭头指向被引用方';
  selected=view.edge?{a:view.edge[0],b:view.edge[1]}:null;
  navigation();$('scope-title').textContent=scope?(mode==='architecture'?nameOf(scope):short(scope)):(mode==='architecture'?architecture.title:'源码依赖总览');
  document.body.classList.toggle('architecture-mode',mode==='architecture');
  $('scope-description').textContent=mode==='architecture'?(components.get(scope)?.description||'先看系统的职责与边界，再进入子架构。'):(scope||'从真实代码计算结构，沿着依赖回到源码。');
  const crumbs=$('breadcrumbs');crumbs.replaceChildren(button(data.project,()=>showScope('')));
  if(scope)scope.split('/').forEach((part,i,all)=>{const key=all.slice(0,i+1).join('/');crumbs.append(el('span','/'),button(mode==='architecture'?nameOf(key):part,()=>showScope(key)));});
  buildGraph();selected=pairs.find(p=>p.a===selected?.a&&p.b===selected?.b)||null;relations();
  const item=evidenceItem(view.import);
  document.body.classList.toggle('detail-open',Boolean(view.comparison||view.coverage||selected||item||view.file));
  if(view.comparison)comparison();else if(view.coverage)coverage();else if(selected)edgeDetails(selected,item?view.import:undefined);else if(item) {fileDetails(item.source,item.line);} else if(view.file)fileDetails(view.file,Number.isInteger(view.line)?Math.max(1,Math.min(files.get(view.file)?.lines||1,view.line)):1);else scopeDetails();
  $('details').scrollTop=0;
  $('details').parentElement.scrollTop=0;
}
$('title').textContent=data.project+' / 代码结构';document.title=data.project+' · Perry 代码结构';
$('snapshot').textContent='SNAPSHOT '+data.snapshot.slice(0,12)+' · 本地离线报告';
for(const [value,name] of [[data.summary.files,'Python 文件'],[data.summary.scripts,'无后缀脚本'],[data.summary.edges,'文件依赖'],[data.summary.parsed+'/'+data.summary.files,'解析覆盖'],[data.summary.unresolved+data.summary.ambiguous+data.issues.length,'需核对记录 / 见扫描范围']]){const s=el('div',undefined,'stat');s.append(el('strong',value),el('span',name));$('stats').append(s);}
$('stats').append(el('div','结构来自代码；职责与设计意图仍由人判断。所有关系都可追溯到源码。','stat-note'));
$('comparison').onclick=()=>state({scope,comparison:true});
$('search').oninput=navigation;$('coverage').onclick=()=>state({scope,coverage:true});
$('close-details').onclick=()=>showScope(scope);
$('architecture-view').onclick=()=>state({mode:'architecture',scope:''});
$('file-view').onclick=()=>state({mode:'files',scope:''});
$('boundary').onchange=()=>state({scope,boundary:$('boundary').checked});
$('mermaid').onclick=()=>{
  const visiblePairs=pairs.filter(p=>mode==='files'||boundary||(inside(p.a,scope)&&inside(p.b,scope)));
  const ids=[...new Set([...localNodes(),...visiblePairs.flatMap(p=>[p.a,p.b])])];
  const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;');
  const lines=['flowchart TB',...ids.map((id,i)=>`  n${i}["${escape(nameOf(id))}"]`),...visiblePairs.map(p=>`  n${ids.indexOf(p.a)} -->|"静态引用 · ${p.ids.size} 条记录"| n${ids.indexOf(p.b)}`)];
  const url=URL.createObjectURL(new Blob([lines.join('\n')+'\n'],{type:'text/plain'}));
  const a=el('a');a.href=url;a.download=data.project+'-architecture.mmd';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
$('download').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=data.project+'-architecture.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
window.addEventListener('hashchange',render);render();
