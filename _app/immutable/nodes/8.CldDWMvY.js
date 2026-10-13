import{s as Jt,d as o,a as Pe,i as f,b as h,c as m,e as c,h as Qt,f as g,g as ot,j as F,k as ne,l as N,m as d,n as $,t as ie,o as Ot,p as Ut,q as Bt,r as Gt,u as Kt,v as Te}from"../chunks/scheduler.D4YX0UhB.js";import{S as Yt,i as Xt,d as D,t as k,a as b,c as dt,m as P,b as S,e as O,g as wt}from"../chunks/index.BZ9FNsSl.js";import{D as Lt,e as Wt,s as Zt,Q as gt,p as er,C as X,a as At,r as Ft,b as tr}from"../chunks/VennDiagram.svelte_svelte_type_style_lang.DUHwGNCu.js";import{w as rr}from"../chunks/entry.DA1siJL1.js";import{h as Se}from"../chunks/setTrackProxy.Cyfckp0w.js";import{p as nr}from"../chunks/stores.Bh-lhyK9.js";import{G as ir,Q as ht,B as $t}from"../chunks/BigValue.BBVm2eyc.js";import{p as ar}from"../chunks/profile.BW8tN6E9.js";function or(p){let n,a=v.title+"",r;return{c(){n=$("h1"),r=ie(a),this.h()},l(s){n=g(s,"H1",{class:!0});var l=F(n);r=ne(l,a),l.forEach(o),this.h()},h(){m(n,"class","title")},m(s,l){f(s,n,l),h(n,r)},p:Te,d(s){s&&o(n)}}}function sr(p){return{c(){this.h()},l(n){this.h()},h(){document.title="Evidence"},m:Te,p:Te,d:Te}}function lr(p){let n,a,r,s,l;return document.title=n=v.title,{c(){a=d(),r=$("meta"),s=d(),l=$("meta"),this.h()},l(i){a=c(i),r=g(i,"META",{property:!0,content:!0}),s=c(i),l=g(i,"META",{name:!0,content:!0}),this.h()},h(){var i,t;m(r,"property","og:title"),m(r,"content",((i=v.og)==null?void 0:i.title)??v.title),m(l,"name","twitter:title"),m(l,"content",((t=v.og)==null?void 0:t.title)??v.title)},m(i,t){f(i,a,t),f(i,r,t),f(i,s,t),f(i,l,t)},p(i,t){t&0&&n!==(n=v.title)&&(document.title=n)},d(i){i&&(o(a),o(r),o(s),o(l))}}}function _r(p){var l,i;let n,a,r=(v.description||((l=v.og)==null?void 0:l.description))&&ur(),s=((i=v.og)==null?void 0:i.image)&&mr();return{c(){r&&r.c(),n=d(),s&&s.c(),a=ot()},l(t){r&&r.l(t),n=c(t),s&&s.l(t),a=ot()},m(t,w){r&&r.m(t,w),f(t,n,w),s&&s.m(t,w),f(t,a,w)},p(t,w){var E,L;(v.description||(E=v.og)!=null&&E.description)&&r.p(t,w),(L=v.og)!=null&&L.image&&s.p(t,w)},d(t){t&&(o(n),o(a)),r&&r.d(t),s&&s.d(t)}}}function ur(p){let n,a,r,s,l;return{c(){n=$("meta"),a=d(),r=$("meta"),s=d(),l=$("meta"),this.h()},l(i){n=g(i,"META",{name:!0,content:!0}),a=c(i),r=g(i,"META",{property:!0,content:!0}),s=c(i),l=g(i,"META",{name:!0,content:!0}),this.h()},h(){var i,t,w;m(n,"name","description"),m(n,"content",v.description??((i=v.og)==null?void 0:i.description)),m(r,"property","og:description"),m(r,"content",((t=v.og)==null?void 0:t.description)??v.description),m(l,"name","twitter:description"),m(l,"content",((w=v.og)==null?void 0:w.description)??v.description)},m(i,t){f(i,n,t),f(i,a,t),f(i,r,t),f(i,s,t),f(i,l,t)},p:Te,d(i){i&&(o(n),o(a),o(r),o(s),o(l))}}}function mr(p){let n,a,r;return{c(){n=$("meta"),a=d(),r=$("meta"),this.h()},l(s){n=g(s,"META",{property:!0,content:!0}),a=c(s),r=g(s,"META",{name:!0,content:!0}),this.h()},h(){var s,l;m(n,"property","og:image"),m(n,"content",At((s=v.og)==null?void 0:s.image)),m(r,"name","twitter:image"),m(r,"content",At((l=v.og)==null?void 0:l.image))},m(s,l){f(s,n,l),f(s,a,l),f(s,r,l)},p:Te,d(s){s&&(o(n),o(a),o(r))}}}function Nt(p){let n,a;return n=new ht({props:{queryID:"owner",queryResult:p[0]}}),{c(){O(n.$$.fragment)},l(r){S(n.$$.fragment,r)},m(r,s){P(n,r,s),a=!0},p(r,s){const l={};s&1&&(l.queryResult=r[0]),n.$set(l)},i(r){a||(b(n.$$.fragment,r),a=!0)},o(r){k(n.$$.fragment,r),a=!1},d(r){D(n,r)}}}function fr(p){let n,a,r,s,l,i;return n=new $t({props:{data:p[0],value:"n_provider_orgs",title:"Provider organizations",fmt:"#,##0"}}),r=new $t({props:{data:p[0],value:"n_hospitals",title:"Hospitals",fmt:"#,##0"}}),l=new $t({props:{data:p[0],value:"n_joint_ventures",title:"Joint ventures",fmt:"#,##0"}}),{c(){O(n.$$.fragment),a=d(),O(r.$$.fragment),s=d(),O(l.$$.fragment)},l(t){S(n.$$.fragment,t),a=c(t),S(r.$$.fragment,t),s=c(t),S(l.$$.fragment,t)},m(t,w){P(n,t,w),f(t,a,w),P(r,t,w),f(t,s,w),P(l,t,w),i=!0},p(t,w){const E={};w&1&&(E.data=t[0]),n.$set(E);const L={};w&1&&(L.data=t[0]),r.$set(L);const C={};w&1&&(C.data=t[0]),l.$set(C)},i(t){i||(b(n.$$.fragment,t),b(r.$$.fragment,t),b(l.$$.fragment,t),i=!0)},o(t){k(n.$$.fragment,t),k(r.$$.fragment,t),k(l.$$.fragment,t),i=!1},d(t){t&&(o(a),o(s)),D(n,t),D(r,t),D(l,t)}}}function It(p){let n,a;return n=new ht({props:{queryID:"organizations",queryResult:p[1]}}),{c(){O(n.$$.fragment)},l(r){S(n.$$.fragment,r)},m(r,s){P(n,r,s),a=!0},p(r,s){const l={};s&2&&(l.queryResult=r[1]),n.$set(l)},i(r){a||(b(n.$$.fragment,r),a=!0)},o(r){k(n.$$.fragment,r),a=!1},d(r){D(n,r)}}}function pr(p){let n,a,r,s,l,i,t,w,E,L,C,y,x,z;return n=new X({props:{id:"org_name",title:"Provider organization",wrap:"true"}}),r=new X({props:{id:"org_type_structure",title:"Structure"}}),l=new X({props:{id:"profit_status",title:"Status"}}),t=new X({props:{id:"n_ccns",title:"Hospitals",fmt:"#,##0"}}),E=new X({props:{id:"ownership_depth",title:"Depth",align:"center"}}),C=new X({props:{id:"is_JV",title:"JV?",align:"center"}}),x=new X({props:{id:"n_ultimate_owners",title:"Owners",align:"center"}}),{c(){O(n.$$.fragment),a=d(),O(r.$$.fragment),s=d(),O(l.$$.fragment),i=d(),O(t.$$.fragment),w=d(),O(E.$$.fragment),L=d(),O(C.$$.fragment),y=d(),O(x.$$.fragment)},l(u){S(n.$$.fragment,u),a=c(u),S(r.$$.fragment,u),s=c(u),S(l.$$.fragment,u),i=c(u),S(t.$$.fragment,u),w=c(u),S(E.$$.fragment,u),L=c(u),S(C.$$.fragment,u),y=c(u),S(x.$$.fragment,u)},m(u,T){P(n,u,T),f(u,a,T),P(r,u,T),f(u,s,T),P(l,u,T),f(u,i,T),P(t,u,T),f(u,w,T),P(E,u,T),f(u,L,T),P(C,u,T),f(u,y,T),P(x,u,T),z=!0},p:Te,i(u){z||(b(n.$$.fragment,u),b(r.$$.fragment,u),b(l.$$.fragment,u),b(t.$$.fragment,u),b(E.$$.fragment,u),b(C.$$.fragment,u),b(x.$$.fragment,u),z=!0)},o(u){k(n.$$.fragment,u),k(r.$$.fragment,u),k(l.$$.fragment,u),k(t.$$.fragment,u),k(E.$$.fragment,u),k(C.$$.fragment,u),k(x.$$.fragment,u),z=!1},d(u){u&&(o(a),o(s),o(i),o(w),o(L),o(y)),D(n,u),D(r,u),D(l,u),D(t,u),D(E,u),D(C,u),D(x,u)}}}function jt(p){let n,a;return n=new ht({props:{queryID:"mix",queryResult:p[2]}}),{c(){O(n.$$.fragment)},l(r){S(n.$$.fragment,r)},m(r,s){P(n,r,s),a=!0},p(r,s){const l={};s&4&&(l.queryResult=r[2]),n.$set(l)},i(r){a||(b(n.$$.fragment,r),a=!0)},o(r){k(n.$$.fragment,r),a=!1},d(r){D(n,r)}}}function cr(p){let n,a,r,s,l,i;return n=new X({props:{id:"structure",title:"Structure"}}),r=new X({props:{id:"organizations",title:"Organizations",fmt:"#,##0"}}),l=new X({props:{id:"hospitals",title:"Hospitals",fmt:"#,##0"}}),{c(){O(n.$$.fragment),a=d(),O(r.$$.fragment),s=d(),O(l.$$.fragment)},l(t){S(n.$$.fragment,t),a=c(t),S(r.$$.fragment,t),s=c(t),S(l.$$.fragment,t)},m(t,w){P(n,t,w),f(t,a,w),P(r,t,w),f(t,s,w),P(l,t,w),i=!0},p:Te,i(t){i||(b(n.$$.fragment,t),b(r.$$.fragment,t),b(l.$$.fragment,t),i=!0)},o(t){k(n.$$.fragment,t),k(r.$$.fragment,t),k(l.$$.fragment,t),i=!1},d(t){t&&(o(a),o(s)),D(n,t),D(r,t),D(l,t)}}}function dr(p){let n,a,r,s,l,i,t,w,E=p[0][0].ultimate_owner_name+"",L,C,y,x,z,u,T,W=(p[0][0].owner_state??"an unreported state")+"",ae,G,j,A,qe='<a href="#organizations-owned">Organizations owned</a>',oe,V,K=`Every provider organization that resolves up to this owner. A joint venture
appears here <em class="markdown">and</em> under its other owners.`,J,Q,U,se,I,R='<a href="#organization-mix">Organization mix</a>',Me,le,vt=`How this owner's provider organizations break down by legal structure, as
recorded in PECOS. "OTHER" is CMS's own catch-all value.`,Ve,Re,_e,Je,Z,yt='<a href="#owner-classification">Owner classification</a>',Qe,ue,bt="As flagged by CMS in the All Owners file.",Ue,ee,Ee,kt='<tr class="markdown"><th align="left" class="markdown">Flag</th> <th align="left" class="markdown">Value</th></tr>',st,B,me,fe,Tt="Private equity",lt,ze,Oe=(p[0][0].is_private_equity??"—")+"",Be,_t,pe,ce,Et="REIT",ut,Ce,Le=(p[0][0].is_reit??"—")+"",Ge,mt,de,we,zt="Holding company",ft,xe,Ae=(p[0][0].is_holding_company??"—")+"",Ke,pt,ge,$e,Ct="Chain home office",ct,He,Fe=(p[0][0].is_chain_home_office??"—")+"",Ye,Xe,he,xt='PECOS owner ID <code class="markdown">{owner[0].ultimate_owner_id}</code>.',We,Ne,Ze,ve,Ht='<a href="/pecos_puf_ownership_modeling_experiment/" class="markdown">← All owners</a> · <a href="/pecos_puf_ownership_modeling_experiment/caveats" class="markdown">Caveats</a>',et,ye,qt=`<p class="markdown">⚠️ Owner records are only partly de-duplicated, so a corporate family may
still appear more than once. See <strong class="markdown"><a href="/pecos_puf_ownership_modeling_experiment/caveats" class="markdown">caveats</a></strong>.</p>`,Y,te=typeof v<"u"&&v.title&&v.hide_title!==!0&&or();function Vt(e,_){return typeof v<"u"&&v.title?lr:sr}let Ie=Vt()(p),re=typeof v=="object"&&_r(),H=p[0]&&Nt(p);y=new ir({props:{cols:"3",$$slots:{default:[fr]},$$scope:{ctx:p}}});let q=p[1]&&It(p);U=new Lt({props:{data:p[1],search:"true",rows:"25",$$slots:{default:[pr]},$$scope:{ctx:p}}});let M=p[2]&&jt(p);return _e=new Lt({props:{data:p[2],rows:"10",$$slots:{default:[cr]},$$scope:{ctx:p}}}),{c(){te&&te.c(),n=d(),Ie.c(),a=$("meta"),r=$("meta"),re&&re.c(),s=ot(),l=d(),H&&H.c(),i=d(),t=$("h1"),w=$("a"),L=ie(E),C=d(),O(y.$$.fragment),x=d(),z=$("p"),u=ie("Registered in "),T=$("strong"),ae=ie(W),G=ie("."),j=d(),A=$("h2"),A.innerHTML=qe,oe=d(),V=$("p"),V.innerHTML=K,J=d(),q&&q.c(),Q=d(),O(U.$$.fragment),se=d(),I=$("h2"),I.innerHTML=R,Me=d(),le=$("p"),le.textContent=vt,Ve=d(),M&&M.c(),Re=d(),O(_e.$$.fragment),Je=d(),Z=$("h2"),Z.innerHTML=yt,Qe=d(),ue=$("p"),ue.textContent=bt,Ue=d(),ee=$("table"),Ee=$("thead"),Ee.innerHTML=kt,st=d(),B=$("tbody"),me=$("tr"),fe=$("td"),fe.textContent=Tt,lt=d(),ze=$("td"),Be=ie(Oe),_t=d(),pe=$("tr"),ce=$("td"),ce.textContent=Et,ut=d(),Ce=$("td"),Ge=ie(Le),mt=d(),de=$("tr"),we=$("td"),we.textContent=zt,ft=d(),xe=$("td"),Ke=ie(Ae),pt=d(),ge=$("tr"),$e=$("td"),$e.textContent=Ct,ct=d(),He=$("td"),Ye=ie(Fe),Xe=d(),he=$("p"),he.innerHTML=xt,We=d(),Ne=$("hr"),Ze=d(),ve=$("p"),ve.innerHTML=Ht,et=d(),ye=$("blockquote"),ye.innerHTML=qt,this.h()},l(e){te&&te.l(e),n=c(e);const _=Qt("svelte-2igo1p",document.head);Ie.l(_),a=g(_,"META",{name:!0,content:!0}),r=g(_,"META",{name:!0,content:!0}),re&&re.l(_),s=ot(),_.forEach(o),l=c(e),H&&H.l(e),i=c(e),t=g(e,"H1",{class:!0,id:!0});var je=F(t);w=g(je,"A",{href:!0});var De=F(w);L=ne(De,E),De.forEach(o),je.forEach(o),C=c(e),S(y.$$.fragment,e),x=c(e),z=g(e,"P",{class:!0});var be=F(z);u=ne(be,"Registered in "),T=g(be,"STRONG",{class:!0});var Mt=F(T);ae=ne(Mt,W),Mt.forEach(o),G=ne(be,"."),be.forEach(o),j=c(e),A=g(e,"H2",{class:!0,id:!0,"data-svelte-h":!0}),N(A)!=="svelte-dmyqnx"&&(A.innerHTML=qe),oe=c(e),V=g(e,"P",{class:!0,"data-svelte-h":!0}),N(V)!=="svelte-i5ctpe"&&(V.innerHTML=K),J=c(e),q&&q.l(e),Q=c(e),S(U.$$.fragment,e),se=c(e),I=g(e,"H2",{class:!0,id:!0,"data-svelte-h":!0}),N(I)!=="svelte-pxwmij"&&(I.innerHTML=R),Me=c(e),le=g(e,"P",{class:!0,"data-svelte-h":!0}),N(le)!=="svelte-1jkqds"&&(le.textContent=vt),Ve=c(e),M&&M.l(e),Re=c(e),S(_e.$$.fragment,e),Je=c(e),Z=g(e,"H2",{class:!0,id:!0,"data-svelte-h":!0}),N(Z)!=="svelte-1rf9krr"&&(Z.innerHTML=yt),Qe=c(e),ue=g(e,"P",{class:!0,"data-svelte-h":!0}),N(ue)!=="svelte-adi56p"&&(ue.textContent=bt),Ue=c(e),ee=g(e,"TABLE",{class:!0});var tt=F(ee);Ee=g(tt,"THEAD",{class:!0,"data-svelte-h":!0}),N(Ee)!=="svelte-192av5u"&&(Ee.innerHTML=kt),st=c(tt),B=g(tt,"TBODY",{class:!0});var ke=F(B);me=g(ke,"TR",{class:!0});var rt=F(me);fe=g(rt,"TD",{align:!0,class:!0,"data-svelte-h":!0}),N(fe)!=="svelte-twsei7"&&(fe.textContent=Tt),lt=c(rt),ze=g(rt,"TD",{align:!0,class:!0});var Rt=F(ze);Be=ne(Rt,Oe),Rt.forEach(o),rt.forEach(o),_t=c(ke),pe=g(ke,"TR",{class:!0});var nt=F(pe);ce=g(nt,"TD",{align:!0,class:!0,"data-svelte-h":!0}),N(ce)!=="svelte-udfb1l"&&(ce.textContent=Et),ut=c(nt),Ce=g(nt,"TD",{align:!0,class:!0});var Dt=F(Ce);Ge=ne(Dt,Le),Dt.forEach(o),nt.forEach(o),mt=c(ke),de=g(ke,"TR",{class:!0});var it=F(de);we=g(it,"TD",{align:!0,class:!0,"data-svelte-h":!0}),N(we)!=="svelte-1gb5u4x"&&(we.textContent=zt),ft=c(it),xe=g(it,"TD",{align:!0,class:!0});var Pt=F(xe);Ke=ne(Pt,Ae),Pt.forEach(o),it.forEach(o),pt=c(ke),ge=g(ke,"TR",{class:!0});var at=F(ge);$e=g(at,"TD",{align:!0,class:!0,"data-svelte-h":!0}),N($e)!=="svelte-f7ap3h"&&($e.textContent=Ct),ct=c(at),He=g(at,"TD",{align:!0,class:!0});var St=F(He);Ye=ne(St,Fe),St.forEach(o),at.forEach(o),ke.forEach(o),tt.forEach(o),Xe=c(e),he=g(e,"P",{class:!0,"data-svelte-h":!0}),N(he)!=="svelte-ilz30f"&&(he.innerHTML=xt),We=c(e),Ne=g(e,"HR",{class:!0}),Ze=c(e),ve=g(e,"P",{class:!0,"data-svelte-h":!0}),N(ve)!=="svelte-72svcw"&&(ve.innerHTML=Ht),et=c(e),ye=g(e,"BLOCKQUOTE",{class:!0,"data-svelte-h":!0}),N(ye)!=="svelte-5w0jlm"&&(ye.innerHTML=qt),this.h()},h(){m(a,"name","twitter:card"),m(a,"content","summary_large_image"),m(r,"name","twitter:site"),m(r,"content","@evidence_dev"),m(w,"href","#owner0ultimate_owner_name"),m(t,"class","markdown"),m(t,"id","owner0ultimate_owner_name"),m(T,"class","markdown"),m(z,"class","markdown"),m(A,"class","markdown"),m(A,"id","organizations-owned"),m(V,"class","markdown"),m(I,"class","markdown"),m(I,"id","organization-mix"),m(le,"class","markdown"),m(Z,"class","markdown"),m(Z,"id","owner-classification"),m(ue,"class","markdown"),m(Ee,"class","markdown"),m(fe,"align","left"),m(fe,"class","markdown"),m(ze,"align","left"),m(ze,"class","markdown"),m(me,"class","markdown"),m(ce,"align","left"),m(ce,"class","markdown"),m(Ce,"align","left"),m(Ce,"class","markdown"),m(pe,"class","markdown"),m(we,"align","left"),m(we,"class","markdown"),m(xe,"align","left"),m(xe,"class","markdown"),m(de,"class","markdown"),m($e,"align","left"),m($e,"class","markdown"),m(He,"align","left"),m(He,"class","markdown"),m(ge,"class","markdown"),m(B,"class","markdown"),m(ee,"class","markdown"),m(he,"class","markdown"),m(Ne,"class","markdown"),m(ve,"class","markdown"),m(ye,"class","markdown")},m(e,_){te&&te.m(e,_),f(e,n,_),Ie.m(document.head,null),h(document.head,a),h(document.head,r),re&&re.m(document.head,null),h(document.head,s),f(e,l,_),H&&H.m(e,_),f(e,i,_),f(e,t,_),h(t,w),h(w,L),f(e,C,_),P(y,e,_),f(e,x,_),f(e,z,_),h(z,u),h(z,T),h(T,ae),h(z,G),f(e,j,_),f(e,A,_),f(e,oe,_),f(e,V,_),f(e,J,_),q&&q.m(e,_),f(e,Q,_),P(U,e,_),f(e,se,_),f(e,I,_),f(e,Me,_),f(e,le,_),f(e,Ve,_),M&&M.m(e,_),f(e,Re,_),P(_e,e,_),f(e,Je,_),f(e,Z,_),f(e,Qe,_),f(e,ue,_),f(e,Ue,_),f(e,ee,_),h(ee,Ee),h(ee,st),h(ee,B),h(B,me),h(me,fe),h(me,lt),h(me,ze),h(ze,Be),h(B,_t),h(B,pe),h(pe,ce),h(pe,ut),h(pe,Ce),h(Ce,Ge),h(B,mt),h(B,de),h(de,we),h(de,ft),h(de,xe),h(xe,Ke),h(B,pt),h(B,ge),h(ge,$e),h(ge,ct),h(ge,He),h(He,Ye),f(e,Xe,_),f(e,he,_),f(e,We,_),f(e,Ne,_),f(e,Ze,_),f(e,ve,_),f(e,et,_),f(e,ye,_),Y=!0},p(e,[_]){typeof v<"u"&&v.title&&v.hide_title!==!0&&te.p(e,_),Ie.p(e,_),typeof v=="object"&&re.p(e,_),e[0]?H?(H.p(e,_),_&1&&b(H,1)):(H=Nt(e),H.c(),b(H,1),H.m(i.parentNode,i)):H&&(wt(),k(H,1,1,()=>{H=null}),dt()),(!Y||_&1)&&E!==(E=e[0][0].ultimate_owner_name+"")&&Pe(L,E);const je={};_&1073741825&&(je.$$scope={dirty:_,ctx:e}),y.$set(je),(!Y||_&1)&&W!==(W=(e[0][0].owner_state??"an unreported state")+"")&&Pe(ae,W),e[1]?q?(q.p(e,_),_&2&&b(q,1)):(q=It(e),q.c(),b(q,1),q.m(Q.parentNode,Q)):q&&(wt(),k(q,1,1,()=>{q=null}),dt());const De={};_&2&&(De.data=e[1]),_&1073741824&&(De.$$scope={dirty:_,ctx:e}),U.$set(De),e[2]?M?(M.p(e,_),_&4&&b(M,1)):(M=jt(e),M.c(),b(M,1),M.m(Re.parentNode,Re)):M&&(wt(),k(M,1,1,()=>{M=null}),dt());const be={};_&4&&(be.data=e[2]),_&1073741824&&(be.$$scope={dirty:_,ctx:e}),_e.$set(be),(!Y||_&1)&&Oe!==(Oe=(e[0][0].is_private_equity??"—")+"")&&Pe(Be,Oe),(!Y||_&1)&&Le!==(Le=(e[0][0].is_reit??"—")+"")&&Pe(Ge,Le),(!Y||_&1)&&Ae!==(Ae=(e[0][0].is_holding_company??"—")+"")&&Pe(Ke,Ae),(!Y||_&1)&&Fe!==(Fe=(e[0][0].is_chain_home_office??"—")+"")&&Pe(Ye,Fe)},i(e){Y||(b(H),b(y.$$.fragment,e),b(q),b(U.$$.fragment,e),b(M),b(_e.$$.fragment,e),Y=!0)},o(e){k(H),k(y.$$.fragment,e),k(q),k(U.$$.fragment,e),k(M),k(_e.$$.fragment,e),Y=!1},d(e){e&&(o(n),o(l),o(i),o(t),o(C),o(x),o(z),o(j),o(A),o(oe),o(V),o(J),o(Q),o(se),o(I),o(Me),o(le),o(Ve),o(Re),o(Je),o(Z),o(Qe),o(ue),o(Ue),o(ee),o(Xe),o(he),o(We),o(Ne),o(Ze),o(ve),o(et),o(ye)),te&&te.d(e),Ie.d(e),o(a),o(r),re&&re.d(e),o(s),H&&H.d(e),D(y,e),q&&q.d(e),D(U,e),M&&M.d(e),D(_e,e)}}}const v={title:"Ultimate Owner"};function wr(p,n,a){let r,s;Ot(p,nr,R=>a(18,r=R)),Ot(p,Ft,R=>a(23,s=R));let{data:l}=n,{data:i={},customFormattingSettings:t,__db:w,inputs:E}=l;Ut(Ft,s="74e0936d9972a4cb7e26842a178f52c1",s);let L=Wt(rr(E));Bt(L.subscribe(R=>E=R)),Gt(tr,{getCustomFormats:()=>t.customFormats||[]});const C=(R,Me)=>ar(w.query,R,{query_name:Me});Zt(C);let y=r.params;Kt(()=>!0);let x={initialData:void 0,initialError:void 0},z=Se`select
    ultimate_owner_id,
    ultimate_owner_name,
    owner_state,
    n_provider_orgs,
    n_hospitals,
    n_joint_ventures,
    n_corporation,
    n_llc,
    n_government,
    n_partnership,
    n_nonprofit,
    max_ownership_depth,
    is_private_equity,
    is_reit,
    is_holding_company,
    is_chain_home_office
from pecos.ultimate_owners
where ultimate_owner_id = '${y.ultimate_owner_id}'`,u=`select
    ultimate_owner_id,
    ultimate_owner_name,
    owner_state,
    n_provider_orgs,
    n_hospitals,
    n_joint_ventures,
    n_corporation,
    n_llc,
    n_government,
    n_partnership,
    n_nonprofit,
    max_ownership_depth,
    is_private_equity,
    is_reit,
    is_holding_company,
    is_chain_home_office
from pecos.ultimate_owners
where ultimate_owner_id = '${y.ultimate_owner_id}'`;i.owner_data&&(i.owner_data instanceof Error?x.initialError=i.owner_data:x.initialData=i.owner_data,i.owner_columns&&(x.knownColumns=i.owner_columns));let T,W=!1;const ae=gt.createReactive({callback:R=>{a(0,T=R)},execFn:C},{id:"owner",...x});ae(u,{noResolve:z,...x}),globalThis[Symbol.for("owner")]={get value(){return T}};let G={initialData:void 0,initialError:void 0},j=Se`select
    org_name,
    org_type_structure,
    case proprietary_nonprofit
        when 'N' then 'Nonprofit'
        when 'P' then 'Proprietary'
        else proprietary_nonprofit
    end as profit_status,
    n_ccns,
    ownership_depth,
    is_JV,
    n_ultimate_owners
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
order by n_ccns desc, org_name`,A=`select
    org_name,
    org_type_structure,
    case proprietary_nonprofit
        when 'N' then 'Nonprofit'
        when 'P' then 'Proprietary'
        else proprietary_nonprofit
    end as profit_status,
    n_ccns,
    ownership_depth,
    is_JV,
    n_ultimate_owners
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
order by n_ccns desc, org_name`;i.organizations_data&&(i.organizations_data instanceof Error?G.initialError=i.organizations_data:G.initialData=i.organizations_data,i.organizations_columns&&(G.knownColumns=i.organizations_columns));let qe,oe=!1;const V=gt.createReactive({callback:R=>{a(1,qe=R)},execFn:C},{id:"organizations",...G});V(A,{noResolve:j,...G}),globalThis[Symbol.for("organizations")]={get value(){return qe}};let K={initialData:void 0,initialError:void 0},J=Se`select
    org_type_structure as structure,
    count(*) as organizations,
    sum(n_ccns) as hospitals
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
group by org_type_structure
order by organizations desc`,Q=`select
    org_type_structure as structure,
    count(*) as organizations,
    sum(n_ccns) as hospitals
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
group by org_type_structure
order by organizations desc`;i.mix_data&&(i.mix_data instanceof Error?K.initialError=i.mix_data:K.initialData=i.mix_data,i.mix_columns&&(K.knownColumns=i.mix_columns));let U,se=!1;const I=gt.createReactive({callback:R=>{a(2,U=R)},execFn:C},{id:"mix",...K});return I(Q,{noResolve:J,...K}),globalThis[Symbol.for("mix")]={get value(){return U}},p.$$set=R=>{"data"in R&&a(3,l=R.data)},p.$$.update=()=>{p.$$.dirty&8&&a(4,{data:i={},customFormattingSettings:t,__db:w}=l,i),p.$$.dirty&16&&er.set(Object.keys(i).length>0),p.$$.dirty&262144&&a(5,y=r.params),p.$$.dirty&32&&a(7,z=Se`select
    ultimate_owner_id,
    ultimate_owner_name,
    owner_state,
    n_provider_orgs,
    n_hospitals,
    n_joint_ventures,
    n_corporation,
    n_llc,
    n_government,
    n_partnership,
    n_nonprofit,
    max_ownership_depth,
    is_private_equity,
    is_reit,
    is_holding_company,
    is_chain_home_office
from pecos.ultimate_owners
where ultimate_owner_id = '${y.ultimate_owner_id}'`),p.$$.dirty&32&&a(8,u=`select
    ultimate_owner_id,
    ultimate_owner_name,
    owner_state,
    n_provider_orgs,
    n_hospitals,
    n_joint_ventures,
    n_corporation,
    n_llc,
    n_government,
    n_partnership,
    n_nonprofit,
    max_ownership_depth,
    is_private_equity,
    is_reit,
    is_holding_company,
    is_chain_home_office
from pecos.ultimate_owners
where ultimate_owner_id = '${y.ultimate_owner_id}'`),p.$$.dirty&960&&(z||!W?z||(ae(u,{noResolve:z,...x}),a(9,W=!0)):ae(u,{noResolve:z})),p.$$.dirty&32&&a(11,j=Se`select
    org_name,
    org_type_structure,
    case proprietary_nonprofit
        when 'N' then 'Nonprofit'
        when 'P' then 'Proprietary'
        else proprietary_nonprofit
    end as profit_status,
    n_ccns,
    ownership_depth,
    is_JV,
    n_ultimate_owners
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
order by n_ccns desc, org_name`),p.$$.dirty&32&&a(12,A=`select
    org_name,
    org_type_structure,
    case proprietary_nonprofit
        when 'N' then 'Nonprofit'
        when 'P' then 'Proprietary'
        else proprietary_nonprofit
    end as profit_status,
    n_ccns,
    ownership_depth,
    is_JV,
    n_ultimate_owners
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
order by n_ccns desc, org_name`),p.$$.dirty&15360&&(j||!oe?j||(V(A,{noResolve:j,...G}),a(13,oe=!0)):V(A,{noResolve:j})),p.$$.dirty&32&&a(15,J=Se`select
    org_type_structure as structure,
    count(*) as organizations,
    sum(n_ccns) as hospitals
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
group by org_type_structure
order by organizations desc`),p.$$.dirty&32&&a(16,Q=`select
    org_type_structure as structure,
    count(*) as organizations,
    sum(n_ccns) as hospitals
from pecos.owner_organizations
where ultimate_owner_id = '${y.ultimate_owner_id}'
group by org_type_structure
order by organizations desc`),p.$$.dirty&245760&&(J||!se?J||(I(Q,{noResolve:J,...K}),a(17,se=!0)):I(Q,{noResolve:J}))},[T,qe,U,l,i,y,x,z,u,W,G,j,A,oe,K,J,Q,se,r]}class zr extends Yt{constructor(n){super(),Xt(this,n,wr,dr,Jt,{data:3})}}export{zr as component};
