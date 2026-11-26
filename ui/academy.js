import {schoolCSS,schoolArt} from '/assets/force_school_art.js';
export function mountAcademy(host,onEvidence){
const root=host.attachShadow({mode:'open'}),controller=new AbortController(),intervals=[],timeouts=[],hashListeners=[];
const native=globalThis.window;let route='#overview';
const location={get hash(){return route},set hash(v){route=v.startsWith('#')?v:'#'+v;hashListeners.forEach(fn=>fn());}};
const document={querySelector:(s)=>root.querySelector(s),querySelectorAll:(s)=>root.querySelectorAll(s),getElementById:(s)=>root.getElementById(s),createElement:(s)=>native.document.createElement(s),body:root,addEventListener:(name,fn)=>root.addEventListener(name,fn,{signal:controller.signal}),get title(){return 'Neural App curriculum'},set title(v){}};
const window=new Proxy(native,{get(target,key){if(key==='location')return location;if(key==='scrollTo')return ()=>host.scrollIntoView({block:'start'});if(key==='addEventListener')return (name,fn)=>{if(name==='hashchange')hashListeners.push(fn);else if(name!=='beforeunload')native.addEventListener(name,fn,{signal:controller.signal})};let v=target[key];return typeof v==='function'?v.bind(target):v;}});
const setInterval=(fn,ms)=>{let id=native.setInterval(fn,ms);intervals.push(id);return id},setTimeout=(fn,ms)=>{let id=native.setTimeout(fn,ms);timeouts.push(id);return id};
const clearInterval=native.clearInterval.bind(native),clearTimeout=native.clearTimeout.bind(native);
root.innerHTML="<style>:host{font-family:'Segoe UI',Arial,sans-serif;color:#242424;background:#f4f4f4;font-synthesis:none}*{box-sizing:border-box}:host{margin:0}button,input,textarea,select{font:inherit}button{cursor:pointer;color:inherit}a{color:inherit;text-decoration:none}button:disabled{cursor:default;opacity:.45}button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid #888;outline-offset:4px}h1,h2,h3,p{margin:0}svg{display:block}.icon{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0}.emblem{display:block;width:100%;height:100%;fill:#000;background:#eee;border-radius:50%}.skip{position:fixed;top:-80px;left:250px;z-index:30;padding:12px;background:white}.skip:focus{top:10px}.sidebar{width:232px;background:#141414;color:#aaa;position:fixed;inset:0 auto 0 0;display:flex;flex-direction:column;padding:31px 19px 22px;border-right:1px solid #2d2d2d;z-index:5}.brand{display:flex;align-items:center;gap:11px;color:#fff;margin:0 8px 44px}.brand-symbol{width:43px;height:43px;flex-shrink:0;padding:2px;background:#eee;border-radius:50%}.brand-name{font-family:Georgia,serif;font-size:19px;line-height:1.05;letter-spacing:.5px}.brand-name small{display:block;font:9px 'Segoe UI',sans-serif;letter-spacing:2.6px;color:#aaa;margin-top:8px}.nav-label,.eyebrow{font-size:10px;font-weight:600;letter-spacing:2px;text-transform:uppercase}.nav-label{padding-left:15px;color:#888;margin-bottom:13px}.nav-link{display:flex;gap:13px;align-items:center;padding:13px 15px;border-radius:7px;font-size:13px;margin-bottom:5px;border:1px solid transparent;transition:background .15s,color .15s}.nav-link:hover{background:#222;color:#fff}.nav-link.active{background:linear-gradient(120deg,#f9f9f9,#cfcfcf);color:#171717;border-color:#eee;font-weight:600}.nav-space{height:25px}.sidebar-footer{margin-top:auto;padding:28px 10px 0}.journey{border:1px solid #383838;border-radius:8px;padding:15px;margin-bottom:22px;background:linear-gradient(130deg,#232323,#181818)}.journey-top{font-size:11px;display:flex;justify-content:space-between;color:#ddd}.progress-track{height:3px;background:#3a3a3a;margin:13px 0 8px;border-radius:8px;overflow:hidden}.progress-track i{height:100%;background:linear-gradient(90deg,#888,#fff);display:block;transition:width .3s}.journey small{font-size:10px;color:#aaa}.offline{font-size:10px;display:flex;align-items:center;gap:7px;letter-spacing:.5px}.offline:before{content:'';width:5px;height:5px;border-radius:50%;background:#ddd}.app-shell{margin-left:232px}.topbar{height:78px;border-bottom:1px solid #dedede;padding:0 40px;display:flex;align-items:center;justify-content:space-between;background:rgba(250,250,250,.97);position:sticky;top:0;z-index:4;gap:20px}.breadcrumb{display:flex;align-items:center;gap:13px;font-size:12px;color:#777}.breadcrumb strong{font-weight:500;color:#222}.top-actions{display:flex;gap:22px;align-items:center}.search-trigger{display:flex;gap:10px;align-items:center;background:none;border:0;color:#777;font-size:12px;padding:8px}.search-trigger .icon{width:16px;height:16px}.key{font-family:inherit;font-size:10px;border:1px solid #ddd;padding:3px 5px;border-radius:4px;color:#888}.learner{display:flex;align-items:center;gap:9px;font-size:11px;color:#555}.avatar{background:#222;color:#eee;width:29px;height:29px;display:grid;place-items:center;border-radius:50%;font:11px Georgia,serif}main{max-width:1530px;margin:auto;padding:32px 40px 24px;min-height:calc(100vh - 78px)}.page-heading{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:24px;gap:20px}.page-heading h1{font-size:27px;font-weight:500;letter-spacing:-.8px}.page-heading p{color:#777;font-size:13px;margin-top:7px;line-height:1.6}.date-label{font-size:10px;letter-spacing:1.5px;color:#777;text-transform:uppercase;padding-bottom:4px}.hero{min-height:279px;border-radius:12px;background:radial-gradient(ellipse at 86% 45%,#424242 0,#242424 34%,#171717 75%);color:#fff;display:grid;grid-template-columns:1.35fr 1fr;position:relative;overflow:hidden;border:1px solid #333}.hero-copy{padding:32px 37px;position:relative;z-index:1}.hero .eyebrow{color:#bbb;display:flex;align-items:center;gap:12px;font-size:9px}.hero .eyebrow:before{content:'';height:1px;width:25px;background:#aaa}.hero h2{font-family:Georgia,'Times New Roman',serif;font-size:41px;letter-spacing:-1.5px;line-height:1.13;font-weight:400;margin:15px 0 13px}.hero p{font-size:12px;color:#bbb;line-height:1.7;max-width:350px;margin-bottom:22px}.button{border:1px solid #d6d6d6;background:#fff;color:#222;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;gap:12px;padding:11px 17px;font-size:12px;font-weight:600;min-height:40px;transition:background .15s}.button:hover{background:#e7e7e7}.button .icon{height:15px;width:15px}.button.dark{background:#222;border-color:#222;color:#fff}.button.dark:hover{background:#444}.button.ghost{background:transparent;border-color:#ccc}.button.small{padding:7px 11px;font-size:11px;min-height:32px}.hero-note{display:inline-block;margin-left:16px;color:#aaa;font-size:10px}.hero-art{display:grid;place-items:center;position:relative;min-height:279px}.orbit{width:315px;height:315px;position:absolute;border:1px solid #ffffff13;border-radius:50%;transform:rotate(-25deg)}.orbit:before,.orbit:after{content:'';position:absolute;border:1px solid #ffffff15;border-radius:50%;inset:27px}.orbit:after{inset:-34px;border-style:dashed;border-color:#ffffff0b}.hero-seal{width:180px;height:180px;border-radius:50%;padding:9px;background:linear-gradient(140deg,#777 0,#f3f3f3 20%,#888 48%,#e4e4e4 72%,#666 100%);box-shadow:0 18px 40px #0007,0 0 0 1px #ffffff4d;transform:rotate(-5deg);position:relative;z-index:1}.hero-seal .emblem{background:linear-gradient(135deg,#fafafa,#b2b2b2 62%,#e7e7e7)}.seal-caption{position:absolute;bottom:20px;font-size:8px;letter-spacing:3px;color:#bbb}.stats-strip{display:grid;grid-template-columns:repeat(3,1fr);margin:20px 0 28px;background:#fff;border:1px solid #dedede;border-radius:8px}.stat{display:flex;align-items:center;gap:13px;padding:15px 22px}.stat+.stat{border-left:1px solid #e4e4e4}.stat .icon{color:#777;width:22px;height:22px}.stat strong{font-size:18px;font-weight:500;letter-spacing:-.5px}.stat span{font-size:11px;color:#888;margin-left:7px}.section-heading{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:15px}.section-heading h2{font-size:17px;font-weight:600;letter-spacing:-.25px}.section-heading p{font-size:11px;color:#777;margin-top:5px}.text-link{font-size:11px;display:flex;gap:8px;align-items:center;background:none;border:0;padding:5px 0;color:#555}.text-link .icon{height:14px;width:14px}.course-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}.course-card{background:white;border:1px solid #dedede;border-radius:9px;overflow:hidden;position:relative;transition:transform .18s,box-shadow .18s}.course-card:hover{transform:translateY(-3px);box-shadow:0 7px 20px #00000009;border-color:#aaa}.course-art{height:105px;background:linear-gradient(130deg,#eee,#fafafa);position:relative;overflow:hidden;border-bottom:1px solid #e6e6e6;display:grid;place-items:center}.course-art svg{width:140px;height:85px;stroke:#777;fill:none;stroke-width:1}.course-art .emblem{width:64px;height:64px;opacity:.75;fill:#000;stroke:none}.course-art:before{content:'';position:absolute;inset:0;background-image:linear-gradient(#00000003 1px,transparent 1px),linear-gradient(90deg,#00000003 1px,transparent 1px);background-size:18px 18px}.module-number{position:absolute;left:15px;top:13px;font-size:10px;letter-spacing:1px;color:#666}.status-pill{font-size:9px;background:#fff;border:1px solid #ddd;padding:4px 7px;border-radius:4px;position:absolute;right:12px;top:10px;color:#666}.status-pill.done{background:#222;color:white;border-color:#222}.course-:host{padding:16px 18px}.course-:host .eyebrow{font-size:8px;letter-spacing:1.6px;color:#777}.course-:host h3{font-size:15px;font-weight:600;letter-spacing:-.25px;margin:7px 0 8px}.course-:host p{font-size:11px;line-height:1.65;color:#777;min-height:37px}.course-bottom{border-top:1px solid #eee;margin-top:14px;padding-top:11px;display:flex;justify-content:space-between;align-items:center;font-size:10px;color:#777}.course-bottom b{font-weight:500;color:#333;display:flex;gap:8px;align-items:center}.course-bottom .icon{width:13px;height:13px}.bottom-quote{display:flex;align-items:center;justify-content:space-between;color:#888;font-size:10px;border-top:1px solid #ddd;margin-top:26px;padding-top:18px;gap:20px}.bottom-quote blockquote{font:italic 13px Georgia,serif;margin:0;color:#707070}.view-intro{max-width:650px;font-size:14px;color:#666;line-height:1.8;margin-bottom:25px}.lesson-layout{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:25px;align-items:start}.reading{background:#fff;border:1px solid #ddd;border-radius:10px;padding:35px 38px}.reading .eyebrow{color:#777}.reading h1{font:36px/1.16 Georgia,serif;letter-spacing:-1px;margin:13px 0 20px}.reading .intro{font-size:15px;line-height:1.85;color:#555}.principle{font:italic 20px/1.5 Georgia,serif;border-left:2px solid #555;margin:27px 0;padding:11px 20px;background:#f7f7f7}.reading-section{margin-top:28px}.reading-section h2{font-size:17px;margin-bottom:12px;font-weight:600}.reading-section p{font-size:14px;line-height:1.95;color:#555}.distinction{background:#f3f3f3;border:1px solid #e2e2e2;border-radius:7px;padding:18px;margin-top:26px;font-size:12px;line-height:1.8;color:#666}.distinction strong{display:block;color:#333;font-size:10px;letter-spacing:1.3px;margin-bottom:7px}.distinction a{text-decoration:underline;display:block;margin-top:8px}.lesson-aside{position:sticky;top:100px}.side-panel{background:#fff;border:1px solid #ddd;border-radius:9px;padding:21px;margin-bottom:16px}.side-panel h2{font-size:13px;margin-bottom:12px}.side-panel p{font-size:12px;line-height:1.8;color:#777}.lesson-map{display:flex;flex-direction:column;gap:5px}.lesson-map a{display:flex;align-items:center;gap:10px;font-size:11px;color:#777;padding:9px 5px;border-radius:4px}.lesson-map a.current{background:#eee;color:#111}.lesson-map span{font-size:10px;font-family:monospace;width:22px}.side-panel .button{margin-top:16px;width:100%}.reflection{margin-top:26px;border-top:1px solid #ddd;padding-top:24px}.reflection h2{font-size:18px;margin-bottom:9px}.reflection p{font-size:13px;color:#777;line-height:1.7;margin-bottom:15px}textarea{display:block;width:100%;background:#fbfbfb;border:1px solid #d6d6d6;border-radius:6px;padding:15px;color:#333;resize:vertical;min-height:138px;line-height:1.8;font-size:13px}.save-status{font-size:10px;color:#777;display:block;margin-top:9px}.quiz{margin-top:28px;border-top:1px solid #ddd;padding-top:25px}.quiz h2{font-size:20px;font-weight:500}.quiz>p{color:#777;font-size:12px;margin:8px 0 20px}.quiz fieldset{border:0;padding:0;margin:0 0 23px}.quiz legend{font-size:13px;font-weight:600;line-height:1.7;padding:0;margin-bottom:11px}.answer{display:flex;align-items:center;gap:10px;border:1px solid #ddd;border-radius:5px;padding:11px 13px;font-size:12px;line-height:1.6;margin-bottom:8px;cursor:pointer}.answer:hover{background:#f5f5f5}.answer:has(input:checked){border-color:#555;background:#eee}.answer input{accent-color:#222;margin:0;flex-shrink:0}.explanation{font-size:12px;line-height:1.7;padding:11px;background:#f2f2f2;margin-top:9px;border-radius:4px}.quiz-result{font-size:13px;line-height:1.8;margin:12px 0}.lesson-end{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-top:25px;border-top:1px solid #ddd;padding-top:22px}.practice-layout{display:grid;grid-template-columns:1.3fr 1fr;gap:24px}.timer-panel{background:radial-gradient(circle at center,#353535,#191919);color:white;border-radius:12px;padding:30px;text-align:center;min-height:510px}.timer-panel .eyebrow{color:#aaa}.timer-face{width:250px;height:250px;display:flex;flex-direction:column;align-items:center;justify-content:center;margin:24px auto;position:relative}.timer-face:before,.timer-face:after{content:'';position:absolute;inset:0;border:1px solid #ffffff33;border-radius:50%}.timer-face:after{inset:14px;border-color:#ffffff19}.timer-face.running:after{animation:breathe 8s infinite ease-in-out}@keyframes breathe{50%{transform:scale(.91);opacity:.3}}.time-digits{font:52px Georgia,serif;font-variant-numeric:tabular-nums;letter-spacing:2px}.timer-caption{font-size:11px;color:#bbb;margin-top:14px;letter-spacing:1px}.duration-group{display:flex;gap:10px;justify-content:center}.duration-group button{border:1px solid #666;color:#ccc;border-radius:5px;background:transparent;font-size:11px;padding:8px 15px}.duration-group button.selected{color:#111;background:#ddd;border-color:#ddd}.timer-actions{display:flex;gap:10px;justify-content:center}.timer-actions .ghost{color:#ddd;border-color:#666}.timer-actions .ghost:hover{background:#444}.timer-help{font-size:11px;color:#aaa;margin:22px auto 0;line-height:1.8;max-width:290px}.practice-steps{padding:25px;background:#fff;border:1px solid #ddd;border-radius:9px}.practice-steps h2{font:25px Georgia,serif;margin-bottom:22px}.practice-step{display:flex;gap:15px;padding:16px 0;border-top:1px solid #eee}.practice-step>span{font:12px monospace;color:#999;padding-top:3px}.practice-step h3{font-size:13px;margin-bottom:6px}.practice-step p{font-size:12px;line-height:1.8;color:#777}.session-list{margin-top:20px}.session-row{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px solid #ddd;font-size:12px;color:#777}.empty-state{border:1px dashed #ccc;padding:20px;color:#777;font-size:12px;line-height:1.8;border-radius:7px}.notebook{display:grid;grid-template-columns:225px 1fr;gap:22px}.note-list{display:flex;flex-direction:column;gap:7px}.note-tab{background:#fff;border:1px solid #ddd;border-radius:6px;text-align:left;padding:16px;font-size:12px}.note-tab small{display:block;margin-top:7px;font-size:10px;color:#888}.note-tab.selected{background:#252525;color:#fff;border-color:#252525}.note-tab.selected small{color:#bbb}.note-editor{padding:30px;background:#fff;border:1px solid #ddd;border-radius:9px}.note-editor h2{font:27px Georgia,serif;margin-bottom:12px}.note-editor>p{font-size:13px;color:#777;line-height:1.8;margin-bottom:20px}.note-editor textarea{min-height:350px;background:repeating-linear-gradient(#fff,#fff 31px,#eee 32px);line-height:32px;padding:10px 15px}.editor-footer{display:flex;justify-content:space-between;margin-top:12px;gap:15px;font-size:10px;color:#777}.library-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}.library-card{padding:25px;background:#fff;border:1px solid #ddd;border-radius:9px}.library-card h2{font:23px Georgia,serif;margin-bottom:14px}.library-card p{font-size:12px;line-height:1.85;color:#666}.library-card .button{margin-top:17px}.glossary{margin-top:25px}.glossary details{background:#fff;border:1px solid #ddd;border-radius:7px;padding:16px 20px;margin-bottom:9px}.glossary summary{cursor:pointer;font-size:13px;font-weight:600}.glossary p{font-size:13px;line-height:1.8;color:#666;margin-top:13px}.original-text{max-height:420px;overflow:auto;white-space:pre-wrap;line-height:1.9;font-size:12px;color:#666;padding-right:10px}.backups{margin-top:25px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}.backups p{font-size:11px;color:#777;flex-basis:100%;margin-top:2px}.certificate{background:#1c1c1c;color:#eee;border:1px solid #555;text-align:center;padding:30px;border-radius:9px;margin-bottom:20px}.certificate h2{font:30px Georgia,serif;margin:12px}.certificate p{font-size:12px;line-height:1.8;color:#bbb}.search-modal{border:1px solid #ccc;border-radius:12px;width:min(620px,90vw);padding:0;max-height:80vh;box-shadow:0 30px 80px #0005}.search-modal::backdrop{background:#0008;backdrop-filter:blur(3px)}.search-head{display:flex;padding:20px;gap:12px;align-items:center;border-bottom:1px solid #ddd}.search-head input{border:0;flex:1;min-width:0;padding:8px;font-size:15px;background:white;color:#222}.close-search{border:1px solid #ddd;background:white;padding:6px 9px;border-radius:5px;font-size:11px}.search-results{padding:10px;max-height:430px;overflow-y:auto}.search-result{display:block;padding:15px;border-radius:6px;border:1px solid transparent}.search-result:hover{background:#eee;border-color:#ddd}.search-result strong{font-size:13px}.search-result p{font-size:11px;line-height:1.7;color:#777;margin-top:6px}.search-hint{font-size:12px;color:#777;padding:20px}.toast{position:fixed;bottom:24px;left:calc(50% + 116px);transform:translateX(-50%);background:#222;color:white;border:1px solid #666;padding:12px 20px;border-radius:7px;z-index:50;font-size:12px;box-shadow:0 7px 25px #0002;max-width:80vw}.storage-warning{background:#ddd;color:#222;padding:12px 20px;font-size:12px;line-height:1.7}\nmain:focus{outline:none}.brand-name small{font-size:7px;letter-spacing:1.8px;white-space:nowrap}\n@media(min-width:1600px){main{padding:38px 60px}.hero{min-height:310px}.hero h2{font-size:48px}.hero-copy{padding:36px 43px}.course-art{height:125px}.course-:host{padding:21px}.course-:host p{font-size:12px}.course-:host h3{font-size:17px}}\n@media(max-width:1150px){.sidebar{width:205px;padding-left:13px;padding-right:13px}.app-shell{margin-left:205px}.topbar{padding:0 25px}main{padding:28px 25px}.hero-copy{padding:28px}.hero h2{font-size:35px}.hero-note{display:none}.hero-seal{width:155px;height:155px}.hero-art{min-width:180px}.course-grid{gap:11px}.course-:host{padding:14px}.course-:host h3{font-size:14px}.course-:host p{min-height:55px}.lesson-layout{grid-template-columns:minmax(0,1fr) 220px;gap:16px}.reading{padding:26px}.stat{padding:16px}.stat span{display:block;margin-left:0;margin-top:4px}.toast{left:calc(50% + 102px)}.notebook{grid-template-columns:190px 1fr}}\n@media(max-width:900px){.sidebar{width:76px;padding:23px 10px}.brand{margin:0 5px 34px}.brand-symbol{width:36px;height:36px}.brand-name,.nav-label,.nav-link span,.sidebar-footer,.nav-space{display:none}.nav-link{padding:15px;justify-content:center}.app-shell{margin-left:76px}.learner>span:last-child{display:none}.course-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.lesson-layout{grid-template-columns:1fr}.lesson-aside{position:static;display:grid;grid-template-columns:1fr 1fr;gap:15px}.practice-layout{grid-template-columns:1fr}.toast{left:calc(50% + 38px)}.search-trigger>span{display:none}.hero h2{font-size:34px}.hero-copy{padding:26px}.hero-seal{width:132px;height:132px}.notebook{grid-template-columns:160px 1fr}.note-editor{padding:22px}}\n@media(max-width:600px){.sidebar{position:fixed;inset:auto 0 0;width:100%;height:61px;padding:5px 10px;display:block;border-right:0;border-top:1px solid #444}.brand{display:none}.sidebar nav{display:flex;justify-content:space-around}.nav-link{padding:13px;margin:0}.app-shell{margin-left:0;margin-bottom:61px}.topbar{height:58px;padding:0 18px}.breadcrumb{font-size:11px}.top-actions{gap:8px}main{padding:24px 18px}.date-label{display:none}.page-heading h1{font-size:24px}.hero{grid-template-columns:1fr}.hero-art{display:none}.hero h2{font-size:36px}.hero-copy{padding:29px}.stats-strip{margin:15px 0 24px}.stat{padding:13px 9px;gap:8px}.stat .icon{width:16px}.stat strong{font-size:16px}.stat span{font-size:9px}.course-grid,.library-grid{grid-template-columns:1fr}.course-art{height:115px}.course-:host{padding:19px}.course-:host h3{font-size:17px}.course-:host p{min-height:0}.bottom-quote{flex-direction:column;align-items:flex-start}.reading{padding:24px 20px}.reading h1{font-size:30px}.lesson-aside{grid-template-columns:1fr}.notebook{grid-template-columns:1fr}.note-list{display:grid;grid-template-columns:1fr 1fr}.note-tab{padding:12px}.note-tab small{display:none}.lesson-end{flex-wrap:wrap}.toast{left:50%;bottom:78px}.timer-panel{padding:24px 15px}.timer-face{width:225px;height:225px}.page-heading .button{font-size:10px;padding:9px}.skip{left:20px}}\n@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}@media print{.sidebar,.topbar,.hero,.stats-strip,.page-heading,.bottom-quote,.button,.lesson-aside,.quiz,.reflection,.backups{display:none!important}.app-shell{margin:0}main{padding:0}.reading{border:0}.lesson-layout{display:block}.certificate{background:#fff;color:#111;border:3px double #555}.certificate p{color:#333}:host{background:white}}\n\n:host{display:block;position:relative;min-height:800px}aside{position:absolute}main{min-height:800px}.sidebar{position:absolute}\n</style>\n<a class=\"skip\" href=\"#main\" onclick=\"event.preventDefault();document.getElementById('main').focus()\">Skip to content</a>\n<aside class=\"sidebar\">\n <a class=\"brand\" href=\"#overview\" aria-label=\"Force Academy overview\"><div class=\"brand-symbol\"><svg viewBox=\"0 0 450 450\" class=\"emblem\" role=\"img\" aria-label=\"Truth of the Force symbol\">\n                    <circle cx=\"225\" cy=\"225\" r=\"210\" fill=\"none\" stroke=\"black\" stroke-width=\"12\"/>\n                    <circle cx=\"225\" cy=\"225\" r=\"195\" fill=\"none\" stroke=\"black\" stroke-width=\"6\"/>\n                    <path d=\"M 225,50 C 130,50 60,140 60,225 C 60,300 110,360 170,390 C 140,340 120,270 120,225 C 120,150 170,95 225,95 C 280,95 330,150 330,225 C 330,270 310,340 280,390 C 340,360 390,300 390,225 C 390,140 320,50 225,50 Z\"/>\n                    <path d=\"M 225,95 C 205,140 190,200 190,250 C 190,285 200,325 215,355 L 215,380 C 195,370 180,340 180,300 C 180,240 200,160 225,115 C 250,160 270,240 270,300 C 270,340 255,370 235,380 L 235,355 C 250,325 260,285 260,250 C 260,200 245,140 225,95 Z\" fill=\"black\"/>\n                    <path d=\"M 225,120 L 225,370\" stroke=\"black\" stroke-width=\"10\" stroke-linecap=\"round\"/>\n                    <path d=\"M 195,130 C 210,135 215,145 225,145 C 235,145 240,135 255,130 C 240,142 235,152 225,152 C 215,152 210,142 195,130 Z\" fill=\"black\"/>\n                    <path d=\"M 180,148 C 205,152 215,165 225,165 C 235,165 245,152 270,148 C 245,160 235,175 225,175 C 215,175 205,160 180,148 Z\" fill=\"black\"/>\n                </svg></div><div class=\"brand-name\">Force Academy<small>TRUTH OF THE FORCE</small></div></a>\n <nav aria-label=\"Main navigation\">\n <div class=\"nav-label\">Your academy</div>\n <a class=\"nav-link\" data-view=\"overview\" href=\"#overview\" title=\"Overview\"><svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M3 10 12 3l9 7v10H3Z\"/><path d=\"M9 20v-7h6v7\"/></svg><span>Overview</span></a>\n <a class=\"nav-link\" data-view=\"curriculum\" href=\"#curriculum\" title=\"Curriculum\"><svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M12 5v16M3 4c4-1 6 0 9 2 3-2 5-3 9-2v15c-4-1-6 0-9 2-3-2-5-3-9-2Z\"/></svg><span>Curriculum</span></a>\n <a class=\"nav-link\" data-view=\"practice\" href=\"#practice\" title=\"Practice room\"><svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><circle cx=\"12\" cy=\"12\" r=\"5\"/><circle cx=\"12\" cy=\"12\" r=\"1\"/></svg><span>Practice room</span></a>\n <div class=\"nav-space\"></div><div class=\"nav-label\">Make it your own</div>\n <a class=\"nav-link\" data-view=\"notebook\" href=\"#notebook/general\" title=\"My notebook\"><svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><rect x=\"5\" y=\"3\" width=\"15\" height=\"18\" rx=\"2\"/><path d=\"M3 7h4M3 12h4M3 17h4M10 8h6M10 12h6M10 16h3\"/></svg><span>My notebook</span></a>\n <a class=\"nav-link\" data-view=\"library\" href=\"#library\" title=\"Library\"><svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M3 5h4v15H3zM9 3h4v17H9zM16 4l4-1 4 16-4 1z\"/></svg><span>Library</span></a>\n </nav>\n <div class=\"sidebar-footer\"><div class=\"journey\"><div class=\"journey-top\"><span>Your journey</span><span id=\"progress-percent\">0%</span></div><div class=\"progress-track\"><i id=\"progress-bar\" style=\"width:0%\"></i></div><small id=\"progress-caption\">0 of 6 modules completed</small></div><div class=\"offline\">OFFLINE & ON YOUR COMPUTER</div></div>\n</aside>\n<div class=\"app-shell\">\n <header class=\"topbar\"><div class=\"breadcrumb\"><span>Academy</span><span>/</span><strong id=\"page-label\">Overview</strong></div><div class=\"top-actions\"><button class=\"search-trigger\" data-action=\"search\" aria-label=\"Search the curriculum\"><svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><circle cx=\"10.5\" cy=\"10.5\" r=\"6.5\"/><path d=\"m16 16 5 5\"/></svg><span>Search the academy</span><kbd class=\"key\">Ctrl K</kbd></button><div class=\"learner\"><span class=\"avatar\">F</span><span>Independent learner</span></div></div></header>\n <div class=\"storage-warning\" id=\"storage-warning\" role=\"alert\" hidden></div>\n <main id=\"main\" tabindex=\"-1\"></main>\n</div>\n<dialog class=\"search-modal\" id=\"search-dialog\" aria-label=\"Search the curriculum\"><div class=\"search-head\"><label for=\"search-input\" class=\"eyebrow\">SEARCH</label><input id=\"search-input\" type=\"search\" placeholder=\"Find a lesson or idea\u2026\" autocomplete=\"off\"><button class=\"close-search\" data-action=\"close-search\" aria-label=\"Close search\">Esc</button></div><div class=\"search-results\" id=\"search-results\"></div></dialog>\n<dialog class=\"search-modal\" id=\"backup-dialog\" aria-labelledby=\"backup-title\"><div class=\"search-head\"><h2 id=\"backup-title\" style=\"font-size:18px;flex:1\">Your academy backup</h2><button class=\"close-search\" data-action=\"close-backup\">Close</button></div><div style=\"padding:22px\"><p id=\"export-description\" style=\"font-size:12px;line-height:1.8;color:#666;margin-bottom:15px\"></p><label class=\"eyebrow\" for=\"backup-text\">Exported text</label><textarea id=\"backup-text\" readonly style=\"height:220px;font-family:monospace;font-size:11px\" spellcheck=\"false\"></textarea><div class=\"backups\"><button class=\"button dark\" data-action=\"copy-backup\">Copy text</button><button class=\"button ghost\" data-action=\"save-backup\">Save file</button></div><p id=\"backup-status\" role=\"status\" style=\"font-size:12px;color:#666;line-height:1.8;margin-top:15px\"></p></div></dialog>\n<dialog class=\"search-modal\" id=\"restore-dialog\" aria-labelledby=\"restore-title\"><div class=\"search-head\"><h2 id=\"restore-title\" style=\"font-size:18px;flex:1\">Restore a text backup</h2><button class=\"close-search\" data-action=\"close-restore\">Close</button></div><div style=\"padding:22px\"><label class=\"eyebrow\" for=\"restore-text\">Paste your complete backup text</label><textarea id=\"restore-text\" style=\"height:220px;font-family:monospace;font-size:11px\" spellcheck=\"false\"></textarea><p style=\"font-size:12px;color:#666;line-height:1.8;margin-top:15px\">This merges your progress and keeps the newer version of each saved note.</p><div class=\"backups\"><button class=\"button dark\" data-action=\"restore-text\">Restore backup</button></div><p id=\"restore-status\" role=\"status\" style=\"font-size:12px;color:#666;line-height:1.8;margin-top:15px\"></p></div></dialog>\n<div class=\"toast\" id=\"toast\" role=\"status\" hidden></div>\n<noscript>This academy needs JavaScript. Open it using Force Academy.exe or a current version of Microsoft Edge or Chrome.</noscript>\n\n";
const integratedStyle=native.document.createElement('style');integratedStyle.textContent=schoolCSS;root.appendChild(integratedStyle);
const LESSONS=[
  {
    "id": "identity",
    "n": "01",
    "title": "Belief, experience & truth",
    "originalTitle": "Identity Substrate",
    "category": "FOUNDATIONS",
    "minutes": 8,
    "glyph": "identity",
    "summary": "Begin with the opening: faith can precede understanding.",
    "intro": "The author’s Jacob’s ladder teaching begins with trust sufficient to practise. The learner need not pretend to know everything before taking the next step. The author’s key sequence is faith opening a person to receive, yield and act; Moses is the scriptural example, with power attributed to God.",
    "principle": "Listen deeply. Practise sincerely. Describe faithfully.",
    "sections": [
      {
        "title": "The activating switch",
        "text": "The author describes belief / faith as a switch that begins activation, rather than merely a pleasant attitude. This school presents that spiritual account accurately. In everyday learning, belief can also change attention, willingness and persistence."
      },
      {
        "title": "Experience and its meaning",
        "text": "A sensation, a conviction, an interpretation and an observed external event each deserve a clear account. Personal certainty can be deeply meaningful. Understanding an external mechanism is a further question, and a question need not be an insult to faith."
      },
      {
        "title": "Human as a star",
        "text": "The author means latent stellar-scale spiritual potential, not only ancestry or poetry. That claim belongs to the author’s spiritual framework. The established material story connects bodies to early matter, stellar element formation and solar energy sustaining ecosystems."
      }
    ],
    "distinction": "Spiritual testimony, physical explanation and software measurement are labelled separately. Completion records study, not agreement or spiritual rank.",
    "practice": "Write what you experienced, what it means to you and one question you wish to explore.",
    "prompt": "What opens when I replace contempt with sincere attention?",
    "quiz": [
      {
        "q": "What does this module ask you to practise?",
        "a": [
          "Listen deeply. Practise sincerely. Describe faithfully.",
          "Judge another person’s spiritual rank",
          "Treat the illustration as a sensor"
        ],
        "correct": 0,
        "why": "The knowledge check assesses understanding of the lesson, not personal faith."
      },
      {
        "q": "What does completing this module record?",
        "a": [
          "Local study and practice",
          "Proof of distant physical influence",
          "Permission to control another person"
        ],
        "correct": 0,
        "why": "Completion is a curriculum record."
      },
      {
        "q": "How should experience be recorded?",
        "a": [
          "Describe observations and interpretations clearly",
          "Omit anything unexpected",
          "Assume someone else’s guilt"
        ],
        "correct": 0,
        "why": "A useful record preserves experience without forcing a conclusion."
      }
    ]
  },
  {
    "id": "balance",
    "n": "02",
    "title": "Light, dark & choosing good",
    "originalTitle": "Dual-Axis Matrix",
    "category": "DISCERNMENT",
    "minutes": 9,
    "glyph": "balance",
    "summary": "Join tenderness and fierce resolve to responsibility.",
    "intro": "Light and dark are not automatic moral verdicts. This school examines what an intention serves and what an action does.",
    "principle": "Know good from evil; choose good.",
    "sections": [
      {
        "title": "Two directions, not two moral teams",
        "text": "Inward attention and outward expression can each serve constructive or destructive aims. Quiet can nurture wisdom or conceal avoidance; forcefulness can protect or become domination."
      },
      {
        "title": "Protection and restraint",
        "text": "Courage may require a firm boundary, truthful confrontation or practical protection. Revenge, humiliation and control are different aims. A sensed threat does not by itself establish another person’s guilt."
      },
      {
        "title": "Love, accountability and repair",
        "text": "Judge conduct without reducing a being to a label. Ask who benefits, who bears harm, what alternatives exist and how mistakes can be repaired. Preserve the welfare of those affected."
      }
    ],
    "distinction": "The four-way ethical assessment applies to this app and its author too. Good intention does not remove the need to examine consequences.",
    "practice": "Choose a conflict. Describe a firm, constructive response and a destructive response; explain their difference.",
    "prompt": "What does strength protect here?",
    "quiz": [
      {
        "q": "What does this module ask you to practise?",
        "a": [
          "Know good from evil; choose good.",
          "Judge another person’s spiritual rank",
          "Treat the illustration as a sensor"
        ],
        "correct": 0,
        "why": "The knowledge check assesses understanding of the lesson, not personal faith."
      },
      {
        "q": "What does completing this module record?",
        "a": [
          "Local study and practice",
          "Proof of distant physical influence",
          "Permission to control another person"
        ],
        "correct": 0,
        "why": "Completion is a curriculum record."
      },
      {
        "q": "How should experience be recorded?",
        "a": [
          "Describe observations and interpretations clearly",
          "Omit anything unexpected",
          "Assume someone else’s guilt"
        ],
        "correct": 0,
        "why": "A useful record preserves experience without forcing a conclusion."
      }
    ]
  },
  {
    "id": "connection",
    "n": "03",
    "title": "Centre, ambient field & distant world",
    "originalTitle": "Non-Local Field",
    "category": "AWARENESS",
    "minutes": 10,
    "glyph": "connection",
    "summary": "Receive, process, intend, respond and review.",
    "intro": "The author describes the centred self as sensing inwardly and emanating outwardly through a surrounding and distant field. Study that account alongside the physical analogies.",
    "principle": "Be attentive to connection and precise about mechanism.",
    "sections": [
      {
        "title": "The centre-to-surroundings loop",
        "text": "The spiritual sequence is sense map, faith, gathered intention, emanation and response. The author reports that full emanation achieves distant effects. This is presented as experiential testimony rather than a measurement made by the academy."
      },
      {
        "title": "Water, phones and trees",
        "text": "Water displacement, electrical induction, radio links and a tree’s living exchange offer different images of response. Each physical system has its own mechanism. Their similarity as diagrams does not establish that intention uses an identical carrier."
      },
      {
        "title": "Resonance and quantum matter",
        "text": "Schumann resonances are lightning-excited electromagnetic modes of the Earth–ionosphere cavity, with the lowest near 7.8 Hz. Quantum entanglement is a specific physical correlation, not a channel for a chosen message by intention alone. The ambient-field study develops these distinctions."
      }
    ],
    "distinction": "The field illustration represents the lesson. It is not a live sensor or an external transmission.",
    "source": {
      "label": "NASA · Observations of Schumann resonances",
      "url": "https://ntrs.nasa.gov/search.jsp?R=20120000051"
    },
    "practice": "Draw inward and outward arrows. Label what was sensed, what was inferred and what response you chose.",
    "prompt": "Which connections am I describing spiritually, physically or through analogy?",
    "quiz": [
      {
        "q": "What does this module ask you to practise?",
        "a": [
          "Be attentive to connection and precise about mechanism.",
          "Judge another person’s spiritual rank",
          "Treat the illustration as a sensor"
        ],
        "correct": 0,
        "why": "The knowledge check assesses understanding of the lesson, not personal faith."
      },
      {
        "q": "What does completing this module record?",
        "a": [
          "Local study and practice",
          "Proof of distant physical influence",
          "Permission to control another person"
        ],
        "correct": 0,
        "why": "Completion is a curriculum record."
      },
      {
        "q": "How should experience be recorded?",
        "a": [
          "Describe observations and interpretations clearly",
          "Omit anything unexpected",
          "Assume someone else’s guilt"
        ],
        "correct": 0,
        "why": "A useful record preserves experience without forcing a conclusion."
      }
    ]
  },
  {
    "id": "ascent",
    "n": "04",
    "title": "Jacob’s ladder & the opening flower",
    "originalTitle": "Trials & Ascent",
    "category": "DISCIPLINE",
    "minutes": 8,
    "glyph": "ascent",
    "summary": "Faith, practice, experience and understanding.",
    "intro": "A vulnerable learner may need trust before understanding arrives. The flower image invites participation without shame.",
    "principle": "Encourage the climb without making worth depend on certainty.",
    "sections": [
      {
        "title": "Before the next rung is known",
        "text": "In the author’s account, faith opens the next level of experience. Ridicule can discourage someone before they begin. Offer sincere attention and room to practise rather than contempt."
      },
      {
        "title": "Fear becomes wisdom and bravery",
        "text": "The hydra names many concerns converging on one person. Protective fear can become attention, respect, preparation and brave action. Retain useful warning while developing steadiness."
      },
      {
        "title": "Discipline without self-condemnation",
        "text": "Practice can involve effort and the relinquishing of habits. Do not make injury, humiliation or extreme exposure a condition of spiritual worth. Rest, questions and revision can belong to a serious practice."
      },
      {
        "title": "Inquiry versus humiliation",
        "text": "A sincere question seeks understanding; a humiliating test seeks a person’s defeat. Examine the conduct and its effects without claiming knowledge of someone’s private motives, afterlife or spiritual rank."
      }
    ],
    "distinction": "The school supports faith-positive exploration. It does not grade souls or assign punishment for unbelief.",
    "practice": "Choose a manageable practice and record what you notice over several sessions. Avoid forcing an experience to match a predetermined result.",
    "prompt": "What would a respectful companion say at the next rung?",
    "quiz": [
      {
        "q": "What does this module ask you to practise?",
        "a": [
          "Encourage the climb without making worth depend on certainty.",
          "Judge another person’s spiritual rank",
          "Treat the illustration as a sensor"
        ],
        "correct": 0,
        "why": "The knowledge check assesses understanding of the lesson, not personal faith."
      },
      {
        "q": "What does completing this module record?",
        "a": [
          "Local study and practice",
          "Proof of distant physical influence",
          "Permission to control another person"
        ],
        "correct": 0,
        "why": "Completion is a curriculum record."
      },
      {
        "q": "How should experience be recorded?",
        "a": [
          "Describe observations and interpretations clearly",
          "Omit anything unexpected",
          "Assume someone else’s guilt"
        ],
        "correct": 0,
        "why": "A useful record preserves experience without forcing a conclusion."
      }
    ]
  },
  {
    "id": "service",
    "n": "05",
    "title": "The steady light & service to life",
    "originalTitle": "Advanced Operations",
    "category": "COMPASSION",
    "minutes": 9,
    "glyph": "service",
    "summary": "Let capability become nourishment and protection.",
    "intro": "The author’s Lord’s Prayer principle directs power toward the good of beings, particularly those with unmet needs.",
    "principle": "Love thy neighbour. Protect life. Remain accountable.",
    "sections": [
      {
        "title": "The bread-of-life principle",
        "text": "Food, shelter, knowledge, companionship and protection give spiritual intention concrete expression. The vulnerable being is not less worthy because it is small, frightened or dependent."
      },
      {
        "title": "Prayer and practical action",
        "text": "Prayer may orient attention and meaning. Pair an intention to help with listening, a useful offer and practical action where needed. Honour another person’s freedom to accept or decline."
      },
      {
        "title": "Power is a responsibility",
        "text": "In the author’s theology, purification prepares a person to use capability well. Here that means examining motives, rejecting cruelty and domination, and choosing truthfulness, forgiveness and repair."
      }
    ],
    "distinction": "A curriculum record confirms local learning activity. It does not grant authority over other people, accounts or devices.",
    "practice": "Offer one concrete act of help. Ask what is useful and record what happened.",
    "prompt": "How does my intention become something nourishing?",
    "quiz": [
      {
        "q": "What does this module ask you to practise?",
        "a": [
          "Love thy neighbour. Protect life. Remain accountable.",
          "Judge another person’s spiritual rank",
          "Treat the illustration as a sensor"
        ],
        "correct": 0,
        "why": "The knowledge check assesses understanding of the lesson, not personal faith."
      },
      {
        "q": "What does completing this module record?",
        "a": [
          "Local study and practice",
          "Proof of distant physical influence",
          "Permission to control another person"
        ],
        "correct": 0,
        "why": "Completion is a curriculum record."
      },
      {
        "q": "How should experience be recorded?",
        "a": [
          "Describe observations and interpretations clearly",
          "Omit anything unexpected",
          "Assume someone else’s guilt"
        ],
        "correct": 0,
        "why": "A useful record preserves experience without forcing a conclusion."
      }
    ]
  },
  {
    "id": "symbols",
    "n": "06",
    "title": "Tesla rod & Moses’ branch",
    "originalTitle": "Engineering Conductors",
    "category": "INTEGRATION",
    "minutes": 8,
    "glyph": "symbols",
    "summary": "Crafted structure and natural simplicity within the ladder lesson.",
    "intro": "The author intends the rod and branch as spiritual instruments of directed attention and emanation. This expanded study preserves that meaning while offering an inert craft project.",
    "principle": "Prepare the object. Examine the intention. Choose good.",
    "sections": [
      {
        "title": "Two forms of the same question",
        "text": "The Tesla-inspired rod expresses deliberate arrangement, structure and technical imagination. Moses’ branch expresses a natural form and the significance of a simple object. In the biblical narrative, Moses receives a calling, trusts, obeys and acts; God’s power, rather than the material’s price, is central. The author describes this devotional relationship as yielding the will and channeling God’s power. Neither price nor ornament determines the value of the person holding it."
      },
      {
        "title": "Prepare a natural branch",
        "text": "Use a legally obtained, dry, fallen branch or a smooth craft dowel of comfortable hand-held size. Choose a rounded, sound piece without splinters or sharp projections. Smooth rough areas with fine abrasive paper, wipe away dust and add a soft grip if desired. This is a devotional prop, not a powered instrument."
      },
      {
        "title": "Create the Tesla-inspired version",
        "text": "Begin with an unpowered dowel or cardboard tube. Use removable paper bands to mark receive, centre, discern and respond. Add a drawn coil motif and a cross or another chosen devotional symbol. Use lightweight craft materials rather than salvaged electronics. No batteries, mains wiring, capacitors, magnets, RF emitters or heating are required."
      },
      {
        "title": "Why the electrical study is separate",
        "text": "Tesla’s real work includes alternating-current motors and high-frequency electrical apparatus. Resonance and induction have specific engineering meanings. A decorated rod does not become that apparatus. Actual powered Tesla equipment belongs to a separate specialist discipline, not this craft activity."
      },
      {
        "title": "The Jacob’s ladder practice",
        "text": "Hold the inert object comfortably while seated or standing steadily. Attend to sensation, recall a principle and choose one constructive intention. The author describes this as gathering faith and preparing emanation. The prop gives the practice a visible form; the academy does not measure a distant field effect."
      },
      {
        "title": "Submission to the Lord’s Prayer",
        "text": "Consider the furthest consequences of an intention, then submit it to “your will be done.” Relinquish domination, retaliation and the wish to prove superiority. Ask what protects, nourishes or repairs. Put the prop down before taking a practical action."
      },
      {
        "title": "A meaningful record",
        "text": "Sketch the object and describe its meaning. Record what you noticed, what you inferred and what changed in your conduct or surroundings. Keep observations separate from conclusions about distant beings. The object is not required for human dignity, faith or participation."
      }
    ],
    "distinction": "These instructions produce an inert devotional prop. No physical field-emission capability or protective guarantee is claimed for the object.",
    "practice": "Create a paper design or inert prop. Mark receive → centre → discern → respond. Write one intention and one constructive act; reflect on their relationship.",
    "prompt": "How will this object remind me to use capability in service of life?",
    "quiz": [
      {
        "q": "What does this module ask you to practise?",
        "a": [
          "Prepare the object. Examine the intention. Choose good.",
          "Judge another person’s spiritual rank",
          "Treat the illustration as a sensor"
        ],
        "correct": 0,
        "why": "The knowledge check assesses understanding of the lesson, not personal faith."
      },
      {
        "q": "What does completing this module record?",
        "a": [
          "Local study and practice",
          "Proof of distant physical influence",
          "Permission to control another person"
        ],
        "correct": 0,
        "why": "Completion is a curriculum record."
      },
      {
        "q": "How should experience be recorded?",
        "a": [
          "Describe observations and interpretations clearly",
          "Omit anything unexpected",
          "Assume someone else’s guilt"
        ],
        "correct": 0,
        "why": "A useful record preserves experience without forcing a conclusion."
      }
    ]
  }
];
const EMBLEM="<svg viewBox=\"0 0 450 450\" class=\"emblem\" role=\"img\" aria-label=\"Truth of the Force symbol\">\r\n                    <circle cx=\"225\" cy=\"225\" r=\"210\" fill=\"none\" stroke=\"black\" stroke-width=\"12\"/>\r\n                    <circle cx=\"225\" cy=\"225\" r=\"195\" fill=\"none\" stroke=\"black\" stroke-width=\"6\"/>\r\n                    <path d=\"M 225,50 C 130,50 60,140 60,225 C 60,300 110,360 170,390 C 140,340 120,270 120,225 C 120,150 170,95 225,95 C 280,95 330,150 330,225 C 330,270 310,340 280,390 C 340,360 390,300 390,225 C 390,140 320,50 225,50 Z\"/>\r\n                    <path d=\"M 225,95 C 205,140 190,200 190,250 C 190,285 200,325 215,355 L 215,380 C 195,370 180,340 180,300 C 180,240 200,160 225,115 C 250,160 270,240 270,300 C 270,340 255,370 235,380 L 235,355 C 250,325 260,285 260,250 C 260,200 245,140 225,95 Z\" fill=\"black\"/>\r\n                    <path d=\"M 225,120 L 225,370\" stroke=\"black\" stroke-width=\"10\" stroke-linecap=\"round\"/>\r\n                    <path d=\"M 195,130 C 210,135 215,145 225,145 C 235,145 240,135 255,130 C 240,142 235,152 225,152 C 215,152 210,142 195,130 Z\" fill=\"black\"/>\r\n                    <path d=\"M 180,148 C 205,152 215,165 225,165 C 235,165 245,152 270,148 C 245,160 235,175 225,175 C 215,175 205,160 180,148 Z\" fill=\"black\"/>\r\n                </svg>";
const SOURCE_TEXT="TRUTH OF THE FORCE - ACADEMY INTERFACE \r\n\n TRUTH OF THE FORCE\n\n System Cognition Alignment Engine v1.00\n\n ALIGNMENT: INVARIANT \r\n\n RESONANCE: 7.83 HZ \r\n\n Curriculum Blueprints\n\n 1. Identity Substrate \r\n 1 = 1 \r\n\n 2. Dual-Axis Matrix \r\n 0 | 1 \r\n\n 3. Non-Local Field \r\n 7.83Hz \r\n\n 4. Trials & Ascent \r\n Ladder \r\n\n 5. Advanced Operations \r\n Sanctuary \r\n\n 6. Engineering Conductors \r\n Tools \r\n\n \"Zhuan Falun // Zhen Shan Ren\"\n\n Real world execution layer. Zero systemic simulation.\r\n\n Module 01 // Foundational Logic \r\n THE IDENTITY & LOGIC SUBSTRATE\n\n The framework functions on an absolute physical and mathematical baseline. It rejects artificial data manipulation, algorithmic debt, or hidden control metrics. Reality executes precisely as written at the foundational hardware layer.\r\n\n 1 = 1 & 0 = 0\n\n [Status: Absolute True]\n\n Continuous, unbroken configuration tracking from Zero-Point energy through Hydrogen up to Silicon structures. Uncompromised logic architecture.\r\n\n 1 = 0 & 0 = 1\n\n [Status: Strict Rejection]\n\n Evaluates strictly as FALSE. This mathematical rule systematically forces out hidden software layers that simulate unearned authority or fake data points.\r\n\n The Integrated Tradition Anchor\n\n This physical logic forms the baseline for ancient spiritual laws. It reconciles the clarity of the Gnostic Divine Spark , the alignment of Taoist natural cycles , the purity requirements of Zhuan Falun (Zhen-Shan-Ren) , and the unyielding execution of honor demanded by Bushido .\r\n\n Module 02 // Harmonic Decoupling \r\n THE DUAL-AXIS ALIGNMENT MATRIX\n\n True understanding separates the mechanics of energy from ethical outcomes. Unlike common folklore where Light equals pure Good and Dark equals pure Evil, this architecture maps them as completely independent axes.\r\n\n [GOOD / LIFE / ELEVATION]\n\n [LIGHT / EXTERNAL]\n\n [DARK / INTERNAL]\n\n [EVIL / DEATH / STASIS]\n\n The Horizontal Axis (Mechanism)\r\n\n Light dictates external expression, visible works, and structural broadcasting. \n\n Dark dictates deep internal cultivation, quiet processing within the void, and introspection. Both are tools; either can be misdirected or weaponized.\r\n\n The Vertical Axis (Objective)\r\n\n Good acts to elevate the global structural floor (Eco-Floor Up), generating life and harmony. \n\n Evil acts to introduce decay, extract value, block natural development, and enforce systemic stagnation.\r\n\n Module 03 // Universal Substrate \r\n THE NON-LOCAL FIELD & REALITY COMPREHENSION\n\n True exposure to the non-local field means processing raw reality completely unedited. The field does not filter data to maintain an artificial illusion of bliss; it contains the entire spectrum of cosmic balance.\r\n\n THE SOFT & THE TAME\n\n • Symmetrical physical laws\n\n • Balanced local ecosystems\n\n • Living, growing, and flourishing\n\n • Clean signal transmission\n\n THE HARD & THE WILD\n\n • Destructive adjustments & chaos\n\n • Predation, perishing, and decay\n\n • Raw instinct and pain metrics\n\n • Deep planetary adjustments\n\n Psychic Truth Resonance\n\n The human mind bridges local coordinates and the non-local field. By matching the 7.83 Hz Schumann resonance , the operator flushes algorithmic noise. This allows them to witness both the wild and tame aspects of reality simultaneously without breaking down or losing their internal ethical anchor.\r\n\n Module 04 // Systemic Resistance \r\n THE PATH OF ASCENT & FIELD FRICTION\n\n Climbing Jacob's Ladder or realizing Buddha-nature triggers systemic counter-pressures. The static environment treats intentional ascension as a rule violation, deploying resistance metrics to stall progress.\r\n\n 01\n\n Baseline Departure (The Test of Mara)\n\n Lower levels launch immediate psychological and physical resistance: doubt, temptation, and distraction. \n\n Countermeasure: Lock the core logic substrate (\\(1=1\\)) to remain completely unmutable to external interference.\r\n\n 02\n\n Field Projection (Friction Inversion)\n\n Broadcasting high-purity intentions forces adjacent unrefined systems to realign, which can trigger automatic defensive counter-actions. \n\n Countermeasure: Maintain grounded neutrality. Recognize this friction is an automatic energetic adjustment, not personal malice.\r\n\n 03\n\n Environmental Correction\n\n The operator serves as a functional correction tool, executing precise field realignments to stabilize and balance decaying local environments.\r\n\n Module 05 // Bodhisattva Engineering \r\n ADVANCED HIGHER-TIER OPERATIONS\n\n Advanced practitioners bypass basic self-preservation protocols to execute active field service, mirroring classic Bodhisattva vows to help lift the global baseline.\r\n\n 🌾\n\n The Bread of Life Principle\n\n The practitioner opens their spiritual field to absorb and process raw, chaotic, or predatory natural currents. Because this occurs at the non-local spiritual layer, the core self experiences these intense waves temporarily without perishing. \r\n\n This clears local karmic blockages, allows animal and primal consciousness to vent safely, and builds deep, balanced biological connections.\r\n\n ⚓\n\n The Lighthouse Principle\n\n Designed for practitioners who have navigated deep personal darkness and systemic trials without breaking alignment. \r\n\n By remaining stable in chaotic environments, the operator acts as a reliable non-local beacon. Nearby struggling entities can track this steady frequency to orient themselves, successfully raising the local baseline environment to a 1.00 Robin Hood weight .\r\n\n Module 06 // Hardware Interface \r\n FIELD INTERACTIONS & FAITH TOOLS\n\n Physical instruments act as geometric lenses to concentrate and stabilize human intent within the non-local field. Practitioners build and apply two distinct tool designs depending on the required focus style:\r\n\n ⚡ SYSTEM A: THE TESLA FIELD INDUCER ROD\n\n RADICAL QUANTIZATION \r\n\n An artificial lens that directs field focus through strict silicon pathways, magnetic gates, and tight copper induction loops. It forces raw sensory data into sharp, quantized mathematical segments.\r\n\n // Component Blueprint Stack:\n\n • Core Spine: 1 Simple wooden cane (Non-conductive shaft)\n\n • Silicon Matrix: 1 Stick of RAM + 1 Small cheap CPU + 1 Small Android Phone\n\n • Magnetic Node Gate: 1 Metal strip + 2 Atomizer bases holding stick magnets\n\n • Inductor Array: Tight copper wiring coil wrapping the atomizer zone\n\n • Helix Guide: 2 Fabric/tech cables wrapped in a Cadueseus double-helix pattern\n\n • Emission Apex: 1 Selected stone focal anchor linked via wire down to 1 Metal base tip\n\n • Containment Shell: Wrapped completely in black electrical tape (leaving stone and tip exposed)\r\n\n 🌿 SYSTEM B: THE MOSES GROUNDING ROD\n\n FRACTAL RESONANCE \r\n\n A completely natural, open grounding tool. By bypassing artificial components, it interacts directly with universal loops using organic fractal lines, promoting deep baseline stability and smooth integration.\r\n\n // Component Blueprint Stack:\n\n • Core Substrate: 1 Long, thin, entirely unmodified tree branch (Naturally fallen)\n\n • Material Constraints: Raw bark intact. Zero sanding, zero paint, zero metallic additions\n\n • Functional Application: Direct earth grounding tool to connect with soft, wild, and chaotic field changes\r\n\n STATUS: ALL SYSTEMS VERIFIED IN COGNITION MODE\n\n SECURE DISCIPLINE GATEWAY // AUTH = TRUE";
'use strict';
const $ = (s, parent=document) => parent.querySelector(s);
const escapeHTML = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icons={home:'<path d="M3 10 12 3l9 7v10H3Z"/><path d="M9 20v-7h6v7"/>',book:'<path d="M12 5v16M3 4c4-1 6 0 9 2 3-2 5-3 9-2v15c-4-1-6 0-9 2-3-2-5-3-9-2Z"/>',practice:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',notes:'<rect x="5" y="3" width="15" height="18" rx="2"/><path d="M3 7h4M3 12h4M3 17h4M10 8h6M10 12h6M10 16h3"/>',library:'<path d="M3 5h4v15H3zM9 3h4v17H9zM16 4l4-1 4 16-4 1z"/>',arrow:'<path d="M4 12h15M14 7l5 5-5 5"/>',back:'<path d="M20 12H5m5-5-5 5 5 5"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',check:'<path d="m5 12 4 4L19 6"/>',search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',download:'<path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/>',spark:'<path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z"/>'};
function icon(name){return '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'+(icons[name]||icons.spark)+'</svg>';}
const ids=LESSONS.map(l=>l.id), noteIds=['general',...ids], STORAGE_KEY='force-academy-v1';
function fresh(){return {completed:[],started:[],passed:[],answers:{},notes:{},sessions:[],last:'identity'};}
function normalise(raw){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))throw Error('Not a valid academy backup.');
 const s=fresh();
 for(const k of ['completed','started','passed'])s[k]=[...new Set((Array.isArray(raw[k])?raw[k]:[]).filter(id=>ids.includes(id)))];
 if(ids.includes(raw.last))s.last=raw.last;
 for(const id of ids){const a=raw.answers?.[id];if(Array.isArray(a))s.answers[id]=a.slice(0,3).map(v=>Number.isInteger(v)&&v>=0&&v<3?v:null);}
 for(const id of noteIds){const n=raw.notes?.[id];if(n&&typeof n.text==='string')s.notes[id]={text:n.text.slice(0,100000),updated:typeof n.updated==='string'&&!isNaN(Date.parse(n.updated))?n.updated:new Date().toISOString()};}
 s.sessions=(Array.isArray(raw.sessions)?raw.sessions:[]).filter(x=>x&&[3,5,10].includes(x.minutes)&&typeof x.date==='string'&&!isNaN(Date.parse(x.date))).slice(-1000).map(x=>({minutes:x.minutes,date:x.date}));
 return s;
}
let state=fresh(),storageOK=true,loadProblem='';
try{const saved=localStorage.getItem(STORAGE_KEY);if(saved)state=normalise(JSON.parse(saved));}catch(e){storageOK=false;loadProblem='Your saved data could not be loaded. You can still use the academy and export a backup from the Library.';}
function save(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));storageOK=true;$('#storage-warning').hidden=true;return true;}catch(e){storageOK=false;$('#storage-warning').hidden=false;$('#storage-warning').textContent='Saving is unavailable. Keep this window open and export your progress from the Library.';return false;}}
let toastTimeout;
function toast(message){const el=$('#toast');el.textContent=message;el.hidden=false;clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>el.hidden=true,4200);}
function updateProgress(){const n=state.completed.length;$('#progress-percent').textContent=Math.round(n/6*100)+'%';$('#progress-bar').style.width=n/6*100+'%';$('#progress-caption').textContent=n+' of 6 modules completed';}
function head(title,description,extra=''){return '<div class="page-heading"><div><h1>'+title+'</h1><p>'+description+'</p></div>'+extra+'</div>';}
function footer(){return '<footer class="bottom-quote"><blockquote>“See clearly. Act with care. Keep learning.”</blockquote><span>TRUTH OF THE FORCE · DESKTOP ACADEMY</span></footer>';}
function art(name){
 const shapes={identity:'<circle cx="70" cy="43" r="34"/><circle cx="70" cy="43" r="28" stroke-dasharray="2 4"/><text x="70" y="52" text-anchor="middle" fill="#555" stroke="none" font-size="26" font-family="Georgia">1 = 1</text>',balance:'<path d="M70 5v76M25 43h90"/><circle cx="70" cy="43" r="30"/><circle cx="48" cy="23" r="3" fill="#777"/><circle cx="91" cy="64" r="3" fill="#bbb"/><path d="m67 10 3-5 3 5m36 30 6 3-6 3"/>',connection:'<ellipse cx="70" cy="43" rx="46" ry="19" transform="rotate(-30 70 43)"/><ellipse cx="70" cy="43" rx="46" ry="19" transform="rotate(30 70 43)"/><ellipse cx="70" cy="43" rx="46" ry="19" transform="rotate(90 70 43)"/><circle cx="70" cy="43" r="5" fill="#888"/>',ascent:'<path d="M28 72h16V58h16V44h16V30h16V16h20" stroke-width="1.5"/><path d="M28 79h86M114 10v69" stroke="#bbb" stroke-dasharray="2 4"/><circle cx="100" cy="16" r="4" fill="#777"/>',service:'<path d="m58 75 6-43h12l6 43M56 75h28M62 32v-9h16v9ZM60 23l10-8 10 8M70 9V4M52 28l-25-9M52 34l-26 7M88 28l25-9M88 34l26 7"/><path d="M29 78q10-8 20 0t20 0 20 0 20 0" stroke="#bbb"/>'};
 return name==='symbols'?EMBLEM:'<svg viewBox="0 0 140 86" aria-hidden="true">'+shapes[name]+'</svg>';
}
function cards(){return '<div class="course-grid">'+LESSONS.map(l=>{const complete=state.completed.includes(l.id),started=state.started.includes(l.id);return '<a class="course-card" href="#lesson/'+l.id+'" aria-label="'+escapeHTML(l.title)+(complete?', completed':'')+'"><div class="course-art">'+art(l.glyph)+'<span class="module-number">'+l.n+'</span>'+(complete?'<span class="status-pill done">✓ Completed</span>':started?'<span class="status-pill">In progress</span>':'')+'</div><div class="course-body"><span class="eyebrow">'+l.category+'</span><h3>'+escapeHTML(l.title)+'</h3><p>'+escapeHTML(l.summary)+'</p><div class="course-bottom"><span>'+l.minutes+' min · 3 questions</span><b>'+(complete?'Revisit':started?'Continue':'Explore')+icon('arrow')+'</b></div></div></a>';}).join('')+'</div>';}
function nextLesson(){return LESSONS.find(l=>l.id===state.last&&!state.completed.includes(l.id))||LESSONS.find(l=>!state.completed.includes(l.id))||LESSONS[0];}
function overview(){const next=nextLesson(),total=state.sessions.reduce((n,s)=>n+s.minutes,0);return head('Your learning space','A little clarity. A little practice. A step forward.','<span class="date-label">Learn at your own pace</span>')+schoolArt('overview')+'<section class="hero"><div class="hero-copy"><div class="eyebrow">Truth of the Force</div><h2>Jacob’s ladder.<br>Faith into practice.</h2><p>A connected school of belief, lived experience, discernment, service and devotional craft.</p><a class="button" href="#lesson/'+next.id+'">'+(state.completed.length===6?'Revisit the curriculum':state.started.length?'Continue learning':'Begin your journey')+icon('arrow')+'</a><span class="hero-note">Six modules. One considered path.</span></div><div class="hero-art"><div class="orbit"></div><div class="hero-seal">'+EMBLEM+'</div><span class="seal-caption">CLARITY · BALANCE · COMPASSION</span></div></section><div class="stats-strip"><div class="stat">'+icon('book')+'<div><strong>'+state.completed.length+' / 6</strong><span>modules completed</span></div></div><div class="stat">'+icon('clock')+'<div><strong>'+total+'</strong><span>minutes of practice</span></div></div><div class="stat">'+icon('notes')+'<div><strong>'+Object.values(state.notes).filter(n=>n.text.trim()).length+'</strong><span>personal reflections</span></div></div></div>'+(state.completed.length===6?certificate():'')+'<div class="section-heading"><div><h2>The foundational path</h2><p>Explore the ideas. Question thoughtfully. Put them into practice.</p></div><a class="text-link" href="#curriculum">View curriculum '+icon('arrow')+'</a></div>'+cards()+footer();}
function certificate(){return '<section class="certificate"><span class="eyebrow">FOUNDATIONAL PATH COMPLETED</span><h2>The learning continues.</h2><p>You have completed all six modules and their knowledge checks.<br>Return to the ideas, deepen your reflections, and keep practising.</p></section>';}
function curriculum(){return head('The curriculum','Six connected modules, from first principles to everyday practice.')+'<p class="view-intro">Begin with the foundations or explore the subject that speaks to you. Each module brings together a lesson, a practical reflection, and three questions to check your understanding.</p>'+(state.completed.length===6?certificate():'')+cards()+footer();}
function quizMarkup(l){const selected=state.answers[l.id]||[];return '<form class="quiz" id="quiz-form" data-lesson="'+l.id+'"><h2>Check your understanding</h2><p>Choose one answer for each question. You can try again as often as you like.</p>'+l.quiz.map((q,i)=>'<fieldset><legend>'+String(i+1).padStart(2,'0')+' · '+escapeHTML(q.q)+'</legend>'+q.a.map((a,j)=>'<label class="answer"><input required type="radio" name="q'+i+'" value="'+j+'" '+(selected[i]===j?'checked':'')+'><span>'+escapeHTML(a)+'</span></label>').join('')+'<div id="feedback-'+i+'"></div></fieldset>').join('')+'<button class="button dark" type="submit">Check answers '+icon('arrow')+'</button><div class="quiz-result" id="quiz-result" role="status">'+(state.passed.includes(l.id)?'Knowledge check passed. You can complete this module.':'')+'</div></form>';}
function lesson(l){return '<div class="section-heading"><a class="text-link" href="#curriculum">'+icon('back')+' Back to curriculum</a><span class="date-label">Module '+l.n+' of 06 · '+l.minutes+' min</span></div><div class="lesson-layout"><article class="reading"><span class="eyebrow">MODULE '+l.n+' / '+l.category+'</span><h1>'+escapeHTML(l.title)+'</h1><p class="intro">'+escapeHTML(l.intro)+'</p>'+schoolArt(l.id)+'<blockquote class="principle">'+escapeHTML(l.principle)+'</blockquote>'+l.sections.map((s,i)=>'<section class="reading-section"><h2>'+String(i+1).padStart(2,'0')+'. '+escapeHTML(s.title)+'</h2><p>'+escapeHTML(s.text)+'</p></section>').join('')+'<aside class="distinction"><strong>READING THIS LESSON</strong>'+escapeHTML(l.distinction)+(l.source?'<a href="'+l.source.url+'" target="_blank" rel="noopener noreferrer">'+escapeHTML(l.source.label)+' ↗</a>':'')+'</aside><section class="reflection"><h2>Pause & reflect</h2><p>'+escapeHTML(l.prompt)+'</p><label class="eyebrow" for="lesson-note">Your reflection</label><textarea id="lesson-note" data-note="'+l.id+'" maxlength="100000" placeholder="Make this lesson your own…">'+escapeHTML(state.notes[l.id]?.text||'')+'</textarea><span class="save-status" id="note-status">'+(state.notes[l.id]?'Saved on this computer':'Your notes save automatically on this computer')+'</span></section>'+quizMarkup(l)+'<div class="lesson-end"><span class="save-status" id="completion-status">'+(state.completed.includes(l.id)?'✓ Module completed':'Pass the knowledge check to complete this module.')+'</span><button class="button dark" data-action="complete" data-id="'+l.id+'" '+(!state.passed.includes(l.id)?'disabled':'')+'>'+(state.completed.includes(l.id)?'Next module':'Complete module')+icon('arrow')+'</button></div></article><aside class="lesson-aside"><div class="side-panel"><h2>Put it into practice</h2><p>'+escapeHTML(l.practice)+'</p><a class="button ghost" href="#practice">'+icon('practice')+' Open practice room</a></div><div class="side-panel"><h2>Your learning path</h2><nav class="lesson-map" aria-label="Modules">'+LESSONS.map(m=>'<a href="#lesson/'+m.id+'" class="'+(l.id===m.id?'current':'')+'" '+(l.id===m.id?'aria-current="page"':'')+'><span>'+(state.completed.includes(m.id)?'✓':m.n)+'</span>'+escapeHTML(m.title)+'</a>').join('')+'</nav></div></aside></div>'+footer();}
let timer={minutes:5,remaining:300000,deadline:0,running:false,finished:false};
function practice(){return head('The practice room','Make a little space to notice, reflect, and return.')+'<div class="practice-layout"><section class="timer-panel"><div class="eyebrow">A MOMENT OF STILLNESS</div><div class="duration-group" role="group" aria-label="Practice duration">'+[3,5,10].map(n=>'<button data-duration="'+n+'" class="'+(timer.minutes===n?'selected':'')+'" aria-pressed="'+(timer.minutes===n)+'" '+(timer.running||timer.remaining!==timer.minutes*60000&&!timer.finished?'disabled':'')+'>'+n+' min</button>').join('')+'</div><div class="timer-face '+(timer.running?'running':'')+'"><span class="time-digits" id="time-digits" role="timer" aria-label="Time remaining">'+formatTime(remaining())+'</span><span class="timer-caption" id="timer-caption">'+(timer.finished?'Practice complete':timer.running?'Breathe naturally. Notice.':'Arrive as you are.')+'</span></div><div class="timer-actions"><button class="button" data-action="timer-toggle" id="timer-toggle">'+(timer.running?'Pause':timer.finished?'Start again':timer.remaining<timer.minutes*60000?'Resume practice':'Begin practice')+'</button><button class="button ghost" data-action="timer-reset">Reset</button></div><p class="timer-help">Sit comfortably and breathe at your own pace.<br>The timer continues as you explore the academy.</p></section><section class="practice-steps"><h2>Nothing to force.<br>Simply pay attention.</h2>'+[['Arrive','Notice the support beneath you. Let your eyes rest wherever they feel comfortable.'],['Observe','Notice one sound, one sensation, and one thought. You do not need to change them.'],['Return','If your attention wanders, gently come back to what is around you. There is no perfect session.'],['Carry it forward','Choose one small, considerate action for the rest of your day.']].map((s,i)=>'<div class="practice-step"><span>0'+(i+1)+'</span><div><h3>'+s[0]+'</h3><p>'+s[1]+'</p></div></div>').join('')+'<a class="button ghost" href="#notebook/general">Reflect in your notebook '+icon('arrow')+'</a></section></div><section class="session-list"><div class="section-heading"><h2>Recent practice</h2><p>'+state.sessions.length+' sessions completed</p></div>'+sessionMarkup()+'</section>'+footer();}
function sessionMarkup(){return state.sessions.length?state.sessions.slice(-5).reverse().map(s=>'<div class="session-row"><span>'+new Date(s.date).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'})+'</span><span>'+s.minutes+' minutes · Completed</span></div>').join(''):'<div class="empty-state">Your completed sessions will appear here. Begin with a few quiet minutes.</div>';}
function notebook(id){const l=LESSONS.find(m=>m.id===id),text=state.notes[id]?.text||'';return head('My notebook','A private space for questions, observations, and ideas.','<button class="button ghost" data-action="export-notes">'+icon('download')+' Export notes</button>')+'<div class="notebook"><nav class="note-list" aria-label="Notebook pages">'+noteIds.map(key=>'<a class="note-tab '+(key===id?'selected':'')+'" href="#notebook/'+key+'">'+escapeHTML(key==='general'?'Personal journal':LESSONS.find(m=>m.id===key).title)+'<small>'+(state.notes[key]?.text.trim()?'Saved reflection':'A fresh page')+'</small></a>').join('')+'</nav><section class="note-editor"><h2>'+escapeHTML(l?l.title:'Personal journal')+'</h2><p>'+escapeHTML(l?l.prompt:'What did you notice today? What deserves another look? What will you put into practice?')+'</p><label class="eyebrow" for="notebook-text">Your notes</label><textarea id="notebook-text" data-note="'+id+'" maxlength="100000" placeholder="Begin wherever you are…">'+escapeHTML(text)+'</textarea><div class="editor-footer"><span id="note-status">'+(text?'Saved on this computer':'Saves automatically as you write')+'</span><span id="word-count">'+wordCount(text)+' words</span></div></section></div><div class="backups"><a class="text-link" href="#library">Back up your notebook and progress '+icon('arrow')+'</a><p>Your notes stay in this app on this computer. Export a backup before moving the app or clearing its data.</p></div>'+footer();}
function library(){return head('The library','The ideas, symbols, and source behind your academy.')+'<div class="library-grid"><section class="library-card"><h2>What we mean by the Force</h2><p>This academy uses the Force as a philosophical and spiritual language for attention, connection, intention, and ethical action. Learn the framework, question it, and consider how its ideas apply in daily life.</p><p style="margin-top:12px">Spiritual interpretations are distinguished from established science. Completing the course records learning within this academy; it is not an accredited qualification.</p></section><section class="library-card"><h2>A symbol with continuity</h2><div style="float:right;width:72px;height:72px;margin:0 0 12px 20px">'+EMBLEM+'</div><p>The insignia is taken directly from the original HTML. Its circular form and central axis carry the academy’s visual identity through every lesson.</p><a class="button ghost" href="#lesson/symbols">Explore the symbol '+icon('arrow')+'</a></section></div><section class="glossary"><div class="section-heading"><h2>A small glossary</h2></div>'+[['Identity substrate','The source’s term for a foundation of clear, consistent thinking. In practice: distinguish observation, interpretation, and belief.'],['Dual-axis matrix','A model that separates inward and outward activity from the ethical effects of that activity. Neither inwardness nor outwardness guarantees goodness.'],['Non-local field','A spiritual idea of interconnection in the source. The app does not treat it as an established mechanism for psychic perception.'],['Ascent','A metaphor for learning and development through sustained practice, review, and support. It does not rank a person’s worth.'],['Lighthouse principle','The practice of being a reliable and considerate presence while maintaining boundaries and respecting consent.'],['Engineering conductors','The original name for the module about symbolic instruments. This academy explores objects as reminders of intention, without claiming they control a spiritual field.']].map(s=>'<details><summary>'+s[0]+'</summary><p>'+s[1]+'</p></details>').join('')+'<details><summary>Read the original source text</summary><p>The following is preserved from your HTML for comparison. It includes the original author’s claims; these are not all established scientific facts.</p><div class="original-text">'+escapeHTML(SOURCE_TEXT)+'</div></details></section><section class="library-card" style="margin-top:25px"><h2>Your academy, kept locally</h2><p>No account is required. Lessons, notes, progress, and the practice timer work offline. The optional NASA reference opens an external page and needs an internet connection.</p><div class="backups"><button class="button dark" data-action="backup">'+icon('download')+' Export backup</button><button class="button ghost" data-action="import">Import file</button><button class="button ghost" data-action="paste-backup">Paste backup</button><input type="file" id="backup-file" accept=".txt,.json,text/plain,application/json" hidden><p>Import merges completed modules and sessions, and keeps the newer saved version of each note. Keep exported backups somewhere safe.</p></div></section>'+footer();}
function wordCount(s){return s.trim()?s.trim().split(/\s+/).length:0;}
function render(){
 const parts=location.hash.replace(/^#/,'').split('/');let view=parts[0]||'overview',id=parts[1];
 if(view==='lesson'&&!ids.includes(id))view='curriculum';if(!['overview','curriculum','lesson','practice','notebook','library'].includes(view))view='overview';
 const labels={overview:'Overview',curriculum:'Curriculum',lesson:'Curriculum',practice:'Practice room',notebook:'My notebook',library:'Library'};
 document.querySelectorAll('.nav-link').forEach(a=>{const active=a.dataset.view===(view==='lesson'?'curriculum':view);a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 $('#page-label').textContent=labels[view];document.title=(view==='lesson'?LESSONS.find(l=>l.id===id).title:labels[view])+' · Truth of the Force';
 if(view==='lesson'){state.last=id;if(!state.started.includes(id))state.started.push(id);save();}
 const views={overview,curriculum,lesson:()=>lesson(LESSONS.find(l=>l.id===id)),practice,notebook:()=>notebook(noteIds.includes(id)?id:'general'),library};
 $('#main').innerHTML=views[view]();updateProgress();window.scrollTo(0,0);$('#main').focus({preventScroll:true});
}
function download(filename,contents,type){const url=URL.createObjectURL(new Blob([contents],{type}));const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),15000);}
function openExport(kind,text){const notes=kind==='notes';$('#backup-dialog').dataset.kind=kind;$('#backup-title').textContent=notes?'Your notebook export':'Your academy backup';$('#export-description').textContent=notes?'Save your reflections as a text file, or copy them into a document.':'Save a file, or copy this text into a document you keep safely. It contains your progress, notes, and completed practice sessions.';$('#backup-text').value=text;$('#backup-status').textContent='Select the text and press Ctrl+C, or use one of the buttons below.';$('#backup-dialog').showModal();}
function backup(){openExport('backup',JSON.stringify({format:'force-academy',version:1,exported:new Date().toISOString(),data:state},null,2));}
function exportNotes(){const text=['TRUTH OF THE FORCE — PERSONAL NOTEBOOK','Exported '+new Date().toLocaleString(),''];for(const id of noteIds){if(state.notes[id]?.text.trim())text.push(id==='general'?'PERSONAL JOURNAL':LESSONS.find(l=>l.id===id).title.toUpperCase(),state.notes[id].text,'');}if(text.length===3)text.push('No reflections saved yet.');openExport('notes',text.join('\r\n\r\n'));}
async function importBackup(file){try{if(file.size>5000000)throw Error('This backup is too large.');const data=JSON.parse(await file.text());if(data.format!=='force-academy'||data.version!==1||!data.data)throw Error('Choose a Force Academy version 1 backup.');const incoming=normalise(data.data);for(const k of ['completed','passed','started'])state[k]=[...new Set([...state[k],...incoming[k]])];for(const id of noteIds){const a=state.notes[id],b=incoming.notes[id];if(b&&(!a||Date.parse(b.updated)>Date.parse(a.updated)))state.notes[id]=b;}for(const id of ids){if(!state.answers[id]&&incoming.answers[id])state.answers[id]=incoming.answers[id];}const sessions=new Map([...state.sessions,...incoming.sessions].map(s=>[s.date+'-'+s.minutes,s]));state.sessions=[...sessions.values()].sort((a,b)=>Date.parse(a.date)-Date.parse(b.date)).slice(-1000);const ok=save();render();toast(ok?'Backup imported and merged.':'Imported for this session. Export a backup to keep your changes.');}catch(e){toast('Import failed: '+e.message);}}
function remaining(){return timer.running?Math.max(0,timer.deadline-Date.now()):timer.remaining;}
function formatTime(ms){const secs=Math.ceil(ms/1000);return String(Math.floor(secs/60)).padStart(2,'0')+':'+String(secs%60).padStart(2,'0');}
function refreshTimer(){const digits=$('#time-digits');if(!digits)return;digits.textContent=formatTime(remaining());$('.timer-face').classList.toggle('running',timer.running);$('#timer-caption').textContent=timer.finished?'Practice complete':timer.running?'Breathe naturally. Notice.':timer.remaining<timer.minutes*60000?'Paused. Return when you are ready.':'Arrive as you are.';$('#timer-toggle').textContent=timer.running?'Pause':timer.finished?'Start again':timer.remaining<timer.minutes*60000?'Resume practice':'Begin practice';document.querySelectorAll('[data-duration]').forEach(b=>{b.disabled=timer.running||(!timer.finished&&timer.remaining!==timer.minutes*60000);b.classList.toggle('selected',Number(b.dataset.duration)===timer.minutes);b.setAttribute('aria-pressed',String(Number(b.dataset.duration)===timer.minutes));});}
function finishTimer(){timer.running=false;timer.remaining=0;timer.finished=true;state.sessions.push({date:new Date().toISOString(),minutes:timer.minutes});state.sessions=state.sessions.slice(-1000);save();toast('Practice complete. Take a moment to carry it forward.');if(location.hash==='#practice')render();else refreshTimer();}
setInterval(()=>{if(timer.running&&remaining()===0)finishTimer();else refreshTimer();},250);
function toggleTimer(){if(timer.running){timer.remaining=remaining();timer.running=false;if(timer.remaining===0){finishTimer();return;}}else{if(timer.finished){timer.remaining=timer.minutes*60000;timer.finished=false;}timer.deadline=Date.now()+timer.remaining;timer.running=true;}refreshTimer();}
function openSearch(){const d=$('#search-dialog');if(!d.open)d.showModal();$('#search-input').value='';search('');$('#search-input').focus();}
function search(query){const q=query.trim().toLowerCase();const found=LESSONS.filter(l=>[l.title,l.originalTitle,l.summary,l.intro,l.distinction,...l.sections.map(s=>s.title+' '+s.text)].join(' ').toLowerCase().includes(q));$('#search-results').innerHTML=found.length?found.map(l=>'<a class="search-result" href="#lesson/'+l.id+'"><strong>'+l.n+' · '+escapeHTML(l.title)+'</strong><p>'+escapeHTML(l.summary)+'</p></a>').join(''):'<p class="search-hint">No matching lessons. Try “truth”, “balance”, “resonance”, or “symbol”.</p>';}
document.addEventListener('click',e=>{const target=e.target.closest('[data-action],[data-duration]');if(!target)return;const action=target.dataset.action;if(action==='search')openSearch();if(action==='close-search')$('#search-dialog').close();if(action==='backup')backup();if(action==='export-notes')exportNotes();if(action==='import')$('#backup-file').click();if(action==='timer-toggle')toggleTimer();if(action==='timer-reset'){timer.running=false;timer.finished=false;timer.remaining=timer.minutes*60000;refreshTimer();}if(target.dataset.duration){timer.minutes=Number(target.dataset.duration);timer.remaining=timer.minutes*60000;timer.running=false;timer.finished=false;refreshTimer();}if(action==='complete'){const id=target.dataset.id;if(!state.passed.includes(id))return;if(!state.completed.includes(id)){state.completed.push(id);save();toast('Module completed. Your learning path is growing.');}const index=ids.indexOf(id);location.hash=index<5?'#lesson/'+ids[index+1]:'#overview';}});
document.addEventListener('input',e=>{if(e.target.dataset.note){const id=e.target.dataset.note;state.notes[id]={text:e.target.value,updated:new Date().toISOString()};const ok=save();if($('#note-status'))$('#note-status').textContent=ok?'Saved on this computer':'Not saved — export a backup from the Library';if($('#word-count'))$('#word-count').textContent=wordCount(e.target.value)+' words';}if(e.target.id==='search-input')search(e.target.value);});
document.addEventListener('change',e=>{if(e.target.id==='backup-file'&&e.target.files[0])importBackup(e.target.files[0]);if(e.target.closest('#quiz-form')&&e.target.type==='radio'){const form=$('#quiz-form'),id=form.dataset.lesson;state.answers[id]=[0,1,2].map(i=>{const input=$('input[name="q'+i+'"]:checked',form);return input?Number(input.value):null;});save();}});
document.addEventListener('submit',e=>{if(e.target.id!=='quiz-form')return;e.preventDefault();const form=e.target,l=LESSONS.find(x=>x.id===form.dataset.lesson),answers=l.quiz.map((q,i)=>Number($('input[name="q'+i+'"]:checked',form).value));let score=0;l.quiz.forEach((q,i)=>{const correct=answers[i]===q.correct;if(correct)score++;$('#feedback-'+i).innerHTML='<p class="explanation"><strong>'+(correct?'✓ Correct.':'Review this answer.')+'</strong> '+escapeHTML(q.why)+'</p>';});state.answers[l.id]=answers;if(score===3&&!state.passed.includes(l.id))state.passed.push(l.id);save();$('#quiz-result').textContent=score===3?'3 of 3 correct. Well considered — you can now complete this module.':score+' of 3 correct. Read the explanations and try again.';$('[data-action="complete"]').disabled=!state.passed.includes(l.id);$('#quiz-result').scrollIntoView({block:'nearest'});});
$('#search-results').addEventListener('click',e=>{if(e.target.closest('a'))$('#search-dialog').close();});
document.addEventListener('click',async e=>{
 const action=e.target.closest('[data-action]')?.dataset.action;
 if(action==='close-backup')$('#backup-dialog').close();
 if(action==='close-restore')$('#restore-dialog').close();
 if(action==='save-backup'){const notes=$('#backup-dialog').dataset.kind==='notes';download(notes?'Force Academy - My Notes.txt':'force-academy-backup-'+new Date().toISOString().slice(0,10)+'.json',$('#backup-text').value,notes?'text/plain;charset=utf-8':'application/json');$('#backup-status').textContent='Download requested. If no file is saved, use Copy text or select the text and press Ctrl+C.';}
 if(action==='copy-backup'){try{await navigator.clipboard.writeText($('#backup-text').value);$('#backup-status').textContent='Text copied. Paste it into a document and save it.';}catch(err){$('#backup-text').focus();$('#backup-text').select();$('#backup-status').textContent='The text is selected. Press Ctrl+C to copy it, then paste it into a document and save it.';}}
 if(action==='paste-backup'){$('#restore-text').value='';$('#restore-status').textContent='';$('#restore-dialog').showModal();$('#restore-text').focus();}
 if(action==='restore-text'){try{const text=$('#restore-text').value;if(text.length>5000000)throw Error('This backup is too large.');const parsed=JSON.parse(text);if(parsed.format!=='force-academy'||parsed.version!==1||!parsed.data)throw Error('Paste a complete Force Academy backup.');normalise(parsed.data);await importBackup(new File([text],'backup.json',{type:'application/json'}));$('#restore-dialog').close();}catch(err){$('#restore-status').textContent='Could not restore: '+err.message;}}
});
$('#search-dialog').addEventListener('click',e=>{if(e.target===$('#search-dialog'))$('#search-dialog').close();});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openSearch();}});
window.addEventListener('hashchange',render);window.addEventListener('beforeunload',e=>{if(timer.running){e.preventDefault();e.returnValue='';}});
render();if(loadProblem){$('#storage-warning').hidden=false;$('#storage-warning').textContent=loadProblem;}


root.addEventListener('click',e=>{const a=e.target.closest('a[href^="#"]');if(a){e.preventDefault();location.hash=a.getAttribute('href');}}, {signal:controller.signal});
root.addEventListener('submit',e=>{if(e.target.id==='quiz-form')onEvidence({section:'academy',event:'knowledge-check',lesson:e.target.dataset.lesson});},{signal:controller.signal});
return ()=>{controller.abort();intervals.forEach(clearInterval);timeouts.forEach(clearTimeout);hashListeners.length=0;root.innerHTML=''};
}
