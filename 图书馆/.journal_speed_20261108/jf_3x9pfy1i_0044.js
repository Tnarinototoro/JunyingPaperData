(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["object"==typeof document?document.currentScript:void 0,[931067,e=>{function t(){return(t=Object.assign.bind()).apply(null,arguments)}e.s(["f",()=>t])},915874,e=>{e.s(["f",0,function(e,t){if(null==e)return{};var r={};for(var n in e)if(({}).hasOwnProperty.call(e,n)){if(-1!==t.indexOf(n))continue;r[n]=e[n]}return r}])},248881,e=>{var t=e.i(843476);let r=()=>(0,t.jsxs)("svg",{width:"24",height:"24",viewBox:"0 0 24 24",fill:"none",xmlns:"http://www.w3.org/2000/svg",children:[(0,t.jsx)("title",{children:"Institution"}),(0,t.jsx)("path",{fillRule:"evenodd",clipRule:"evenodd",d:"M21.5625 5.76365V9.7499H19.6875V16.4999H21.5625V22.1249H2.4375V16.4999H4.3125V9.7499H2.4375V5.76365L12 0.899902L21.5625 5.76365ZM4.3125 6.91115L12 3.00365L19.6875 6.91115V7.8749H4.3125V6.91115ZM17.8125 18.3749H19.6875V20.2499H4.3125V18.3749H6.1875V9.7499H8.8125V18.3749H10.6875V9.7499H13.3125V18.3749H15.1875V9.7499H17.8125V18.3749Z",fill:"currentColor"})]});var n=e.i(797524);e.s(["f",0,()=>(0,t.jsxs)("div",{className:n.default.titleContainer,children:[(0,t.jsx)(r,{}),(0,t.jsx)("h3",{className:n.default.title,children:"Open access agreement"})]})],248881)},55545,e=>{var t=e.i(843476),r=e.i(913192),n=e.i(211768),i=e.i(5383),a=e.i(271645);e.i(843553);var l=e.i(259209),s=e.i(618566),o=e.i(49321),u=e.i(685149),d=e.i(326472),c=e.i(627818),m=e.i(376545),f=e.i(750376),h=e.i(553686);let p=(e,t)=>{switch(t.type){case"UPDATE_QUERY":return{...e,query:t.payload};case"UPDATE_MODE":return{...e,mode:t.payload};default:return e}},g=()=>{let e=(0,s.useRouter)(),[g]=(0,o.f)(),[y,b]=(0,a.useReducer)(p,{query:g.query,mode:g.mode}),[x,v]=(0,a.useState)(!1),{errors:w,showErrors:$,hasErrors:O}=(0,n.U)({mode:y.mode,fields:{query:y.query}}),j=e=>{b({type:"UPDATE_QUERY",payload:e})},S=e=>{b({type:"UPDATE_MODE",payload:e})},R="recommend-stem"===y.mode?"Enter your abstract":"Enter journal title or subject area",q="results"===(0,d.f)();return(0,t.jsx)(r.P,{$isResultsPage:q,children:(0,t.jsxs)(r.J,{onSubmit:t=>(t=>{if(t.preventDefault(),O)$();else{let t=Object.fromEntries(Object.entries(g).filter(([e,t])=>null!==t));(0,l.z)("contentView",{content:[{id:"jf:find-journals",type:"jf:search:find-journals",format:"MIME-XHTML",title:"Find Journals",detail:`jf:mode:${y.mode}`}]});let r=new URLSearchParams({...t,query:y.query,mode:y.mode});e.push(`${u.s.results()}?${r.toString()}`)}})(t),onReset:()=>j(""),$isResultsPage:q,children:[(0,t.jsxs)(r.S,{children:[(0,t.jsxs)(r.F,{htmlFor:"recommend-stem-radio",children:[(0,t.jsx)(r.d,{type:"radio",id:"recommend-stem-radio",name:"searchMode",value:"recommend-stem",checked:"recommend-stem"===y.mode,onChange:()=>S("recommend-stem")}),"Match my abstract"]}),(0,t.jsxs)(r.F,{htmlFor:"search-radio",children:[(0,t.jsx)(r.d,{type:"radio",id:"search-radio",name:"searchMode",value:"search",checked:"search"===y.mode,onChange:()=>S("search")}),"Search by journal title, subject area, or aims & scope"]})]}),(0,t.jsxs)(r.n,{children:[(0,t.jsxs)(r.z,{children:[(0,t.jsx)(r.p,{name:"query",id:"search-textarea","data-testid":"search-textarea",placeholder:R,value:y.query,minRows:1,maxRows:x?4:1,minLength:n.n[y.mode].query.minLength,$hasError:!!w.query,$isResultsPage:!0,onBlur:()=>{$("query"),v(!1)},onFocus:()=>v(!0),onChange:e=>j(e.target.value)}),""!==y.query&&(0,t.jsx)(f.f,{"data-testid":"clear-search-query","aria-label":"Clear search",type:"reset",variant:"tertiary",iconName:"delete"})]}),(0,t.jsx)(m.f,{className:h.default.button,"data-testid":"find-journals-button",iconRight:q?void 0:"navigate-right",type:"submit",variant:"primary",size:"xxlarge","data-aa-name":c.s.FIND_JOURNALS,label:"Find journals"}),(0,t.jsxs)(r.f,{children:[w.query&&(0,t.jsx)(r.H,{children:w.query}),(0,t.jsx)(i.f,{maxLength:n.n[y.mode].query.maxLength,length:y.query.length})]})]})]})})};g.displayName="SearchForm",e.s(["default",0,g])},913192,211768,5383,e=>{var t=e.i(997053),r=e.i(931067),n=e.i(915874),i=e.i(271645),a=i.useLayoutEffect,l=function(e){var t=i.default.useRef(e);return a(function(){t.current=e}),t},s=function(e,t){"function"==typeof e?e(t):e.current=t},o=function(e,t){var r=i.default.useRef();return i.default.useCallback(function(n){e.current=n,r.current&&s(r.current,null),r.current=t,t&&s(t,n)},[t])},u={"min-height":"0","max-height":"none",height:"0",visibility:"hidden",overflow:"hidden",position:"absolute","z-index":"-1000",top:"0",right:"0",display:"block"},d=function(e){Object.keys(u).forEach(function(t){e.style.setProperty(t,u[t],"important")})},c=null,m=function(e,t){var r=e.scrollHeight;return"border-box"===t.sizingStyle.boxSizing?r+t.borderSize:r-t.paddingSize},f=function(){},h=["borderBottomWidth","borderLeftWidth","borderRightWidth","borderTopWidth","boxSizing","fontFamily","fontSize","fontStyle","fontWeight","letterSpacing","lineHeight","paddingBottom","paddingLeft","paddingRight","paddingTop","tabSize","textIndent","textRendering","textTransform","width","wordBreak","wordSpacing","scrollbarGutter"],p=!!document.documentElement.currentStyle,g=function(e){var t=window.getComputedStyle(e);if(null===t)return null;var r=h.reduce(function(e,r){return e[r]=t[r],e},{}),n=r.boxSizing;if(""===n)return null;p&&"border-box"===n&&(r.width=parseFloat(r.width)+parseFloat(r.borderRightWidth)+parseFloat(r.borderLeftWidth)+parseFloat(r.paddingRight)+parseFloat(r.paddingLeft)+"px");var i=parseFloat(r.paddingBottom)+parseFloat(r.paddingTop),a=parseFloat(r.borderBottomWidth)+parseFloat(r.borderTopWidth);return{sizingStyle:r,paddingSize:i,borderSize:a}};function y(e,t,r){var n=l(r);i.useLayoutEffect(function(){var r=function(e){return n.current(e)};if(e)return e.addEventListener(t,r),function(){return e.removeEventListener(t,r)}},[])}var b=function(e,t){y(document.body,"reset",function(r){e.current.form===r.target&&t(r)})},x=function(e){y(window,"resize",e)},v=function(e){y(document.fonts,"loadingdone",e)},w=["cacheMeasurements","maxRows","minRows","onChange","onHeightChange"],$=i.forwardRef(function(e,t){var a=e.cacheMeasurements,l=e.maxRows,s=e.minRows,u=e.onChange,h=void 0===u?f:u,p=e.onHeightChange,y=void 0===p?f:p,$=(0,n.f)(e,w),O=void 0!==$.value,j=i.useRef(null),S=o(j,t),R=i.useRef(0),q=i.useRef(),U=function(){var e=j.current,t=a&&q.current?q.current:g(e);if(t){q.current=t;var r,n,i,o,u,f,h,p,b,x,v,w=(r=e.value||e.placeholder||"x",void 0===(n=s)&&(n=1),void 0===(i=l)&&(i=1/0),c||((c=document.createElement("textarea")).setAttribute("tabindex","-1"),c.setAttribute("aria-hidden","true"),d(c)),null===c.parentNode&&document.body.appendChild(c),o=t.paddingSize,u=t.borderSize,h=(f=t.sizingStyle).boxSizing,Object.keys(f).forEach(function(e){c.style[e]=f[e]}),d(c),c.value=r,p=m(c,t),c.value=r,p=m(c,t),c.value="x",x=(b=c.scrollHeight-o)*n,"border-box"===h&&(x=x+o+u),p=Math.max(x,p),v=b*i,"border-box"===h&&(v=v+o+u),[p=Math.min(v,p),b]),$=w[0],O=w[1];R.current!==$&&(R.current=$,e.style.setProperty("height",$+"px","important"),y($,{rowHeight:O}))}};return i.useLayoutEffect(U),b(j,function(){if(!O){var e=j.current.value;requestAnimationFrame(function(){var t=j.current;t&&e!==t.value&&U()})}}),x(U),v(U),i.createElement("textarea",(0,r.f)({},$,{onChange:function(e){O||U(),h(e)},ref:S}))}),O=e.i(584984);let{spacing:j,colors:S,breakpoints:R,fontSize:q}=e.i(129704).U,U=t.U.form.withConfig({displayName:"styles__StyledSearchForm",componentId:"sc-a7afdf02-0"})`
  padding: ${e=>e.$isResultsPage?0:`${j.medium} ${j.small}`};
  background-color: ${S.white};

  color: ${S.grey8};

  @media screen and (min-width: ${R.large}) {
    padding: ${e=>e.$isResultsPage?0:`${j.xlarge} ${j.xlarge}`};
  }

  @media screen and (min-width: ${R.xlarge}) {
    padding: ${e=>e.$isResultsPage?0:` ${j.xxlarge} ${j.xxxlarge}`};
  }
`,E=t.U.div.withConfig({displayName:"styles__SearchFormWrapper",componentId:"sc-a7afdf02-1"})`
  margin: ${e=>e.$isResultsPage?0:`${j.xlarge} -${j.small} 0`};
  @media screen and (min-width: ${e=>e.theme.breakpoints.large}) {
    margin: ${e=>e.$isResultsPage?0:`${j.xlarge} -${j.xlarge} 0`};
  }

  @media screen and (min-width: ${e=>e.theme.breakpoints.xlarge}) {
    margin: ${e=>e.$isResultsPage?0:`${j.xlarge} -${j.xxxlarge} 0`};
  }
`,L=t.m`
  display: block;
  background: white;
  border-width: 1px 1px 2px;
  border-color: ${S.grey6};
  outline: none;
  font-size: ${q.small};
  padding: ${j.small} ${j.xlarge} ${j.small} ${j.small};
  line-height: 1.4em;
  width: 100%;
  color: inherit;
  border-radius: 0;

  &:hover,
  &:focus {
    border-color: ${e=>e.$hasError?S.error:S.grey8};
    border-width: 2px;
  }
  &::placeholder {
    color: ${S.grey6};
  }

  ${e=>e.$hasError&&t.m`
      border-color: ${S.error};
      border-width: 2px;
    `}
`,z=(0,t.U)($).withConfig({displayName:"styles__TextArea",componentId:"sc-a7afdf02-2"})`
  ${L}
  min-height: 100%;
  resize: none;
`,k=t.U.p.attrs({role:"alert"}).withConfig({displayName:"styles__InputError",componentId:"sc-a7afdf02-3"})`
  color: ${S.error};
  font-size: ${q.small};
  margin-top: 0;
  margin-bottom: 0;
`,M=t.U.div.withConfig({displayName:"styles__FieldMeta",componentId:"sc-a7afdf02-4"})`
  display: flex;
  flex-flow: row wrap;
  align-items: flex-start;
  grid-row: 2;

  @media screen and (max-width: ${R.medium}) {
    order: 2;
  }
`;t.U.small.withConfig({displayName:"styles__FieldInfo",componentId:"sc-a7afdf02-5"})`
  font-size: ${q.small};
  margin-left: auto;
  color: ${e=>e.limitExceeded?S.error:"inherit"};
  flex-basis: 100%;
  order: -1;
  text-align: right;

  &:not(:first-child) {
    margin-bottom: ${j.xsmall};
  }

  @media screen and (min-width: ${R.small}) {
    font-size: ${q.xsmall};
    flex-basis: auto;
    order: 2;

    &:not(:first-child) {
      margin-bottom: 0;
    }
  }
`;let _=t.U.div.withConfig({displayName:"styles__StyledRadioButtonsWrapper",componentId:"sc-a7afdf02-6"})`
  margin-bottom: ${j.small};
  font-size: ${q.small};
  display: flex;
  align-items: self-start;
  gap: ${j.small};
  @media screen and (max-width: ${R.small}) {
    flex-direction: column;
  }
`,C=t.U.div.withConfig({displayName:"styles__StyledTextAreaContainer",componentId:"sc-a7afdf02-7"})`
  position: relative;
  @media screen and (max-width: ${R.medium}) {
    order: 1;
  }

  button {
    ${O.U.buttonReset};
    position: absolute;
    right: ${j.medium};
    top: 12px;
  }
`,F=t.U.div.withConfig({displayName:"styles__SearchBoxContainer",componentId:"sc-a7afdf02-8"})`
  display: grid;
  grid-template-columns: 3fr 1fr;
  grid-gap: ${j.small};
  @media screen and (max-width: ${R.medium}) {
    display: flex;
    flex-direction: column;
  }
`,I=t.U.label.withConfig({displayName:"styles__StyledRadioLabel",componentId:"sc-a7afdf02-9"})`
  display: flex;
`,P=t.U.input.withConfig({displayName:"styles__StyledRadioButton",componentId:"sc-a7afdf02-10"})`
  height: 20px;
  width: 20px;
  margin: 0 ${j.xsmall} 0 0;
  appearance: none;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 2px ${S.grey6};
  &:hover {
    box-shadow: 0 0 0 2px #000;
  }
  &:checked {
    background-color: ${S.linkBlue};
  }
`;e.s(["f",0,M,"H",0,k,"n",0,F,"P",0,E,"d",0,P,"S",0,_,"F",0,I,"J",0,U,"z",0,C,"p",0,z],913192);var A=e.i(33290);let D={search:{query:{minLength:5,minLengthLatin:3,maxLength:A.U?1500:5e3,label:"search query",required:!0}},"recommend-stem":{query:{minLength:36,minLengthLatin:36,maxLength:A.U?1500:5e3,label:"abstract",required:!0}}},H={query:void 0};e.s(["U",0,e=>{let[t,r]=(0,i.useState)(H),n=(0,i.useMemo)(()=>(({mode:e,fields:t})=>{let r={...H};return Object.entries(t).forEach(([t,n])=>{let{required:i,minLengthLatin:a,minLength:l,maxLength:s,label:o}=D[e][t],u=n.trim(),d=u.replaceAll(/\s/g,""),c=d.replaceAll(/[^a-z]+/gi,"");i&&!d?r[t]=`Please enter ${D[e][t].label}`:l&&d.length<l?r[t]=`Please enter a longer ${D[e][t].label}`:a&&c.length<a?r[t]=`Please enter a longer ${D[e][t].label}, including more latin characters.`:s&&u.length>s&&(r[t]=`Please reduce the length of your ${o}`)}),r})(e),[e]),a=(0,i.useMemo)(()=>Object.values(n).some(e=>void 0!==e),[n]),l=(0,i.useCallback)(e=>{e?r({...t,[e]:n[e]}):r(n)},[n,t]);return(0,i.useEffect)(()=>{let e=!1;Object.entries(t).forEach(([t,r])=>{r&&n[t]!==r&&(e=!0)}),e&&l()},[n,l,t]),{errors:t,showErrors:l,hasErrors:a}},"n",0,D],211768);var T=e.i(843476),N=e.i(672195),V=e.i(145617),W=e.i(343794);e.s(["f",0,({maxLength:e,length:t})=>{if(!e)return null;let r=t>e,n="";return r?n=` (${(0,N.f)(t-e)} too many)`:t>e-50&&(n=` (${(0,N.f)(e-t)} left)`),(0,T.jsx)("small",{className:(0,W.default)(V.default.fieldInfo,{[V.default.fieldInfoLimitExceeded]:r}),children:`Maximum ${(0,N.f)(e)} characters ${n}`})}],5383)},49321,e=>{var t=e.i(86049),r=e.i(947421),n=e.i(589271),i=e.i(618566),a=e.i(680902),l=e.i(622289),s=e.i(271645);function o(e,t,r){try{return e(t)}catch(e){return(0,l.l)("[nuqs] Error while parsing value `%s`: %O"+(r?" (for key `%s`)":""),t,e,r),null}}function u(e){function t(t){if(void 0===t)return null;let r="";if(Array.isArray(t)){if(void 0===t[0])return null;r=t[0]}return"string"==typeof t&&(r=t),o(e.parse,r)}return{type:"single",eq:(e,t)=>e===t,...e,parseServerSide:t,withDefault(e){return{...this,defaultValue:e,parseServerSide:r=>t(r)??e}},withOptions(e){return{...this,...e}}}}let d=u({parse:e=>e,serialize:String});u({parse:e=>{let t=parseInt(e);return t==t?t:null},serialize:e=>""+Math.round(e)}),u({parse:e=>{let t=parseInt(e);return t==t?t-1:null},serialize:e=>""+Math.round(e+1)}),u({parse:e=>{let t=parseInt(e,16);return t==t?t:null},serialize:e=>{let t=Math.round(e).toString(16);return(1&t.length?"0":"")+t}}),u({parse:e=>{let t=parseFloat(e);return t==t?t:null},serialize:String});let c=u({parse:e=>"true"===e.toLowerCase(),serialize:String});function m(e,t){return e.valueOf()===t.valueOf()}function f(e){return u({parse:t=>e.includes(t)?t:null,serialize:String})}u({parse:e=>{let t=parseInt(e);return t==t?new Date(t):null},serialize:e=>""+e.valueOf(),eq:m}),u({parse:e=>{let t=new Date(e);return t.valueOf()==t.valueOf()?t:null},serialize:e=>e.toISOString(),eq:m}),u({parse:e=>{let t=new Date(e.slice(0,10));return t.valueOf()==t.valueOf()?t:null},serialize:e=>e.toISOString().slice(0,10),eq:m});let h=(0,a.r)(),p={};function g(e,t,r,n,i,l){let s=!1,u=Object.entries(e).reduce((e,[u,d])=>{var c;let m=t?.[u]??u,f=n[m],h="multi"===d.type?[]:null,p=void 0===f?("multi"===d.type?r?.getAll(m):r?.get(m))??h:f;return i&&l&&((c=i[m]??h)===p||null!==c&&null!==p&&"string"!=typeof c&&"string"!=typeof p&&c.length===p.length&&c.every((e,t)=>e===p[t]))?e[u]=l[u]??null:(s=!0,e[u]=((0,a.i)(p)?null:o(d.parse,p,m))??null,i&&(i[m]=p)),e},{});if(!s){let t=Object.keys(e),r=Object.keys(l??{});s=t.length!==r.length||t.some(e=>!r.includes(e))}return{state:u,hasChanged:s}}function y(e,t){return Object.fromEntries(Object.keys(e).map(r=>[r,e[r]??t[r]??null]))}let b=(e,t)=>({defaultValue:e,parse:t}),x=(e,r)=>b(e,e=>{let n,{min:i,max:a}=t.y[r];return"string"==typeof e?!isNaN(n=parseInt(e))&&n>=i&&n<=a?n:null:null});e.s(["f",0,()=>{let e=(0,i.useSearchParams)(),{affiliations:t}=(0,r.useAffiliations)(),o=e.get("query")??"",u=e.get("paperAbstract")??"",m="string"==typeof o&&o.length>0?o:"string"==typeof u?u:"",v=t?.authorOrg?t.authorOrg.id:"",[w,$]=function(e,t={}){let r=(0,s.useId)(),n=(0,l.i)(),i=(0,l.a)(),{history:o="replace",scroll:u=n?.scroll??!1,shallow:d=n?.shallow??!0,throttleMs:c=a.s.timeMs,limitUrlUpdates:m=n?.limitUrlUpdates,clearOnDefault:f=n?.clearOnDefault??!0,startTransition:b,urlKeys:x=p}=t,v=Object.keys(e).join(","),w=(0,s.useMemo)(()=>Object.fromEntries(Object.keys(e).map(e=>[e,x[e]??e])),[v,JSON.stringify(x)]),$=(0,l.r)(Object.values(w)),O=$.searchParams,j=(0,s.useRef)({}),S=(0,s.useMemo)(()=>Object.fromEntries(Object.keys(e).map(t=>[t,e[t].defaultValue??null])),[Object.values(e).map(({defaultValue:e})=>e).join(",")]),R=a.t.useQueuedQueries(Object.values(w)),[q,U]=(0,s.useState)(()=>g(e,x,O??new URLSearchParams,R).state),E=(0,s.useRef)(q);if((0,l.c)("[nuq+ %s `%s`] render - state: %O, iSP: %s",r,v,q,O),Object.keys(j.current).join("&")!==Object.values(w).join("&")){let{state:t,hasChanged:n}=g(e,x,O,R,j.current,E.current);n&&((0,l.c)("[nuq+ %s `%s`] State changed: %O",r,v,{state:t,initialSearchParams:O,queuedQueries:R,queryRef:j.current,stateRef:E.current}),E.current=t,U(t)),j.current=Object.fromEntries(Object.entries(w).map(([t,r])=>[r,e[t]?.type==="multi"?O?.getAll(r):O?.get(r)??null]))}(0,s.useEffect)(()=>{let{state:t,hasChanged:n}=g(e,x,O,R,j.current,E.current);n&&((0,l.c)("[nuq+ %s `%s`] State changed: %O",r,v,{state:t,initialSearchParams:O,queuedQueries:R,queryRef:j.current,stateRef:E.current}),E.current=t,U(t))},[Object.values(w).map(e=>`${e}=${O?.getAll(e)}`).join("&"),JSON.stringify(R)]),(0,s.useEffect)(()=>{let t=Object.keys(e).reduce((t,n)=>(t[n]=({state:t,query:i})=>{U(a=>{let{defaultValue:s}=e[n],o=w[n],u=t??s??null;return Object.is(a[n]??s??null,u)?((0,l.c)("[nuq+ %s `%s`] Cross-hook key sync %s: %O (default: %O). no change, skipping, resolved: %O",r,v,o,t,s,E.current),a):(E.current={...E.current,[n]:u},j.current[o]=i,(0,l.c)("[nuq+ %s `%s`] Cross-hook key sync %s: %O (default: %O). updateInternalState, resolved: %O",r,v,o,t,s,E.current),E.current)})},t),{});for(let n of Object.keys(e)){let e=w[n];(0,l.c)("[nuq+ %s `%s`] Subscribing to sync for `%s`",r,e,v),h.on(e,t[n])}return()=>{for(let n of Object.keys(e)){let e=w[n];(0,l.c)("[nuq+ %s `%s`] Unsubscribing to sync for `%s`",r,e,v),h.off(e,t[n])}}},[v,w]);let L=(0,s.useCallback)((t,n={})=>{let s,p=Object.fromEntries(Object.keys(e).map(e=>[e,null])),g="function"==typeof t?t(y(E.current,S))??p:t??p;(0,l.c)("[nuq+ %s `%s`] setState: %O",r,v,g);let x=0,O=!1,j=[];for(let[t,r]of Object.entries(g)){let p=e[t],g=w[t];if(!p||void 0===r)continue;(n.clearOnDefault??p.clearOnDefault??f)&&null!==r&&void 0!==p.defaultValue&&(p.eq??((e,t)=>e===t))(r,p.defaultValue)&&(r=null);let y=null===r?null:(p.serialize??String)(r);h.emit(g,{state:r,query:y});let v={key:g,query:y,options:{history:n.history??p.history??o,shallow:n.shallow??p.shallow??d,scroll:n.scroll??p.scroll??u,startTransition:n.startTransition??p.startTransition??b}};if(n?.limitUrlUpdates?.method==="debounce"||m?.method==="debounce"||p.limitUrlUpdates?.method==="debounce"){!0===v.options.shallow&&console.warn((0,l.s)(422));let e=n?.limitUrlUpdates?.timeMs??m?.timeMs??p.limitUrlUpdates?.timeMs??a.s.timeMs,t=a.t.push(v,e,$,i);x<e&&(s=t,x=e)}else{let e=n?.limitUrlUpdates?.timeMs??p?.limitUrlUpdates?.timeMs??m?.timeMs??n.throttleMs??p.throttleMs??c;j.push(a.t.abort(g)),a.n.push(v,e),O=!0}}let R=j.reduce((e,t)=>t(e),O?a.n.flush($,i):a.n.getPendingPromise($));return s??R},[v,o,d,u,c,m?.method,m?.timeMs,b,w,$.updateUrl,$.getSearchParamsSnapshot,$.rateLimitFactor,i,S]);return[(0,s.useMemo)(()=>y(q,S),[q,S]),L]}({citeScoreGte:x(null,"citeScore"),citeScoreLt:x(null,"citeScore"),impactFactorGte:x(null,"impactFactor"),impactFactorLt:x(null,"impactFactor"),timeToFirstDecisionLt:x(null,"timeToFirstDecision"),timeToAcceptanceLt:x(null,"timeToAcceptance"),goldOpenAccess:c.withDefault(!0),subscription:c.withDefault(!0),sortBy:f(Object.values(n.b)).withDefault(n.b.Default),sortOrder:f(Object.values(n.f)).withDefault(n.f.Ascending),query:d.withDefault(m),mode:b(n.l.RECOMMEND_STEM,e=>e),ecrId:d.withDefault(v),agreementsFilter:f(Object.values(n.R)).withDefault(n.R.ALL_JOURNALS)},{history:"push",clearOnDefault:!1});return[w,$]}],49321)}],313404,e=>{e.v(t=>Promise.all(["static/chunks/03bkyl9z1weg-.js"].map(t=>e.l(t))).then(()=>t(509219)))},413467,e=>{e.v({background:"sH3VnW_background",container:"sH3VnW_container",homeBanners:"sH3VnW_homeBanners",notchWrapper:"sH3VnW_notchWrapper"})},797524,e=>{e.v({title:"h81Tqq_title",titleContainer:"h81Tqq_titleContainer",tooltip:"h81Tqq_tooltip"})},145617,e=>{e.v({fieldInfo:"iVXSQq_fieldInfo",fieldInfoLimitExceeded:"iVXSQq_fieldInfoLimitExceeded"})},553686,e=>{e.v({button:"KdGCSW_button"})}]);