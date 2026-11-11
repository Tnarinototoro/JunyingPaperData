(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["object"==typeof document?document.currentScript:void 0,[931067,e=>{function t(){return(t=Object.assign.bind()).apply(null,arguments)}e.s(["f",()=>t])},915874,e=>{e.s(["f",0,function(e,t){if(null==e)return{};var r={};for(var n in e)if(({}).hasOwnProperty.call(e,n)){if(-1!==t.indexOf(n))continue;r[n]=e[n]}return r}])},11901,e=>{var t=e.i(843476),r=e.i(271645),n=e.i(271070);class a extends r.Component{state={error:void 0,errorInfo:void 0};componentDidCatch(e,t){this.setState({error:e,errorInfo:t}),console.error("An error occurred somewhere in the component tree",e)}renderError(){let{className:e,...r}=this.props;return(0,t.jsx)(n.f,{...r,className:e})}render(){let{children:e}=this.props,{error:t}=this.state;return this.props.error instanceof Error||t?this.renderError():e}}e.s(["ErrorBoundary",0,a])},55545,e=>{var t=e.i(843476),r=e.i(913192),n=e.i(211768),a=e.i(5383),i=e.i(271645);e.i(843553);var s=e.i(259209),l=e.i(618566),o=e.i(49321),u=e.i(685149),d=e.i(326472),c=e.i(627818),m=e.i(376545),f=e.i(750376),p=e.i(553686);let h=(e,t)=>{switch(t.type){case"UPDATE_QUERY":return{...e,query:t.payload};case"UPDATE_MODE":return{...e,mode:t.payload};default:return e}},g=()=>{let e=(0,l.useRouter)(),[g]=(0,o.f)(),[y,b]=(0,i.useReducer)(h,{query:g.query,mode:g.mode}),[x,v]=(0,i.useState)(!1),{errors:S,showErrors:w,hasErrors:O}=(0,n.U)({mode:y.mode,fields:{query:y.query}}),$=e=>{b({type:"UPDATE_QUERY",payload:e})},j=e=>{b({type:"UPDATE_MODE",payload:e})},R="recommend-stem"===y.mode?"Enter your abstract":"Enter journal title or subject area",E="results"===(0,d.f)();return(0,t.jsx)(r.P,{$isResultsPage:E,children:(0,t.jsxs)(r.J,{onSubmit:t=>(t=>{if(t.preventDefault(),O)w();else{let t=Object.fromEntries(Object.entries(g).filter(([e,t])=>null!==t));(0,s.z)("contentView",{content:[{id:"jf:find-journals",type:"jf:search:find-journals",format:"MIME-XHTML",title:"Find Journals",detail:`jf:mode:${y.mode}`}]});let r=new URLSearchParams({...t,query:y.query,mode:y.mode});e.push(`${u.s.results()}?${r.toString()}`)}})(t),onReset:()=>$(""),$isResultsPage:E,children:[(0,t.jsxs)(r.S,{children:[(0,t.jsxs)(r.F,{htmlFor:"recommend-stem-radio",children:[(0,t.jsx)(r.d,{type:"radio",id:"recommend-stem-radio",name:"searchMode",value:"recommend-stem",checked:"recommend-stem"===y.mode,onChange:()=>j("recommend-stem")}),"Match my abstract"]}),(0,t.jsxs)(r.F,{htmlFor:"search-radio",children:[(0,t.jsx)(r.d,{type:"radio",id:"search-radio",name:"searchMode",value:"search",checked:"search"===y.mode,onChange:()=>j("search")}),"Search by journal title, subject area, or aims & scope"]})]}),(0,t.jsxs)(r.n,{children:[(0,t.jsxs)(r.z,{children:[(0,t.jsx)(r.p,{name:"query",id:"search-textarea","data-testid":"search-textarea",placeholder:R,value:y.query,minRows:1,maxRows:x?4:1,minLength:n.n[y.mode].query.minLength,$hasError:!!S.query,$isResultsPage:!0,onBlur:()=>{w("query"),v(!1)},onFocus:()=>v(!0),onChange:e=>$(e.target.value)}),""!==y.query&&(0,t.jsx)(f.f,{"data-testid":"clear-search-query","aria-label":"Clear search",type:"reset",variant:"tertiary",iconName:"delete"})]}),(0,t.jsx)(m.f,{className:p.default.button,"data-testid":"find-journals-button",iconRight:E?void 0:"navigate-right",type:"submit",variant:"primary",size:"xxlarge","data-aa-name":c.s.FIND_JOURNALS,label:"Find journals"}),(0,t.jsxs)(r.f,{children:[S.query&&(0,t.jsx)(r.H,{children:S.query}),(0,t.jsx)(a.f,{maxLength:n.n[y.mode].query.maxLength,length:y.query.length})]})]})]})})};g.displayName="SearchForm",e.s(["default",0,g])},913192,211768,5383,e=>{var t=e.i(997053),r=e.i(931067),n=e.i(915874),a=e.i(271645),i=a.useLayoutEffect,s=function(e){var t=a.default.useRef(e);return i(function(){t.current=e}),t},l=function(e,t){"function"==typeof e?e(t):e.current=t},o=function(e,t){var r=a.default.useRef();return a.default.useCallback(function(n){e.current=n,r.current&&l(r.current,null),r.current=t,t&&l(t,n)},[t])},u={"min-height":"0","max-height":"none",height:"0",visibility:"hidden",overflow:"hidden",position:"absolute","z-index":"-1000",top:"0",right:"0",display:"block"},d=function(e){Object.keys(u).forEach(function(t){e.style.setProperty(t,u[t],"important")})},c=null,m=function(e,t){var r=e.scrollHeight;return"border-box"===t.sizingStyle.boxSizing?r+t.borderSize:r-t.paddingSize},f=function(){},p=["borderBottomWidth","borderLeftWidth","borderRightWidth","borderTopWidth","boxSizing","fontFamily","fontSize","fontStyle","fontWeight","letterSpacing","lineHeight","paddingBottom","paddingLeft","paddingRight","paddingTop","tabSize","textIndent","textRendering","textTransform","width","wordBreak","wordSpacing","scrollbarGutter"],h=!!document.documentElement.currentStyle,g=function(e){var t=window.getComputedStyle(e);if(null===t)return null;var r=p.reduce(function(e,r){return e[r]=t[r],e},{}),n=r.boxSizing;if(""===n)return null;h&&"border-box"===n&&(r.width=parseFloat(r.width)+parseFloat(r.borderRightWidth)+parseFloat(r.borderLeftWidth)+parseFloat(r.paddingRight)+parseFloat(r.paddingLeft)+"px");var a=parseFloat(r.paddingBottom)+parseFloat(r.paddingTop),i=parseFloat(r.borderBottomWidth)+parseFloat(r.borderTopWidth);return{sizingStyle:r,paddingSize:a,borderSize:i}};function y(e,t,r){var n=s(r);a.useLayoutEffect(function(){var r=function(e){return n.current(e)};if(e)return e.addEventListener(t,r),function(){return e.removeEventListener(t,r)}},[])}var b=function(e,t){y(document.body,"reset",function(r){e.current.form===r.target&&t(r)})},x=function(e){y(window,"resize",e)},v=function(e){y(document.fonts,"loadingdone",e)},S=["cacheMeasurements","maxRows","minRows","onChange","onHeightChange"],w=a.forwardRef(function(e,t){var i=e.cacheMeasurements,s=e.maxRows,l=e.minRows,u=e.onChange,p=void 0===u?f:u,h=e.onHeightChange,y=void 0===h?f:h,w=(0,n.f)(e,S),O=void 0!==w.value,$=a.useRef(null),j=o($,t),R=a.useRef(0),E=a.useRef(),T=function(){var e=$.current,t=i&&E.current?E.current:g(e);if(t){E.current=t;var r,n,a,o,u,f,p,h,b,x,v,S=(r=e.value||e.placeholder||"x",void 0===(n=l)&&(n=1),void 0===(a=s)&&(a=1/0),c||((c=document.createElement("textarea")).setAttribute("tabindex","-1"),c.setAttribute("aria-hidden","true"),d(c)),null===c.parentNode&&document.body.appendChild(c),o=t.paddingSize,u=t.borderSize,p=(f=t.sizingStyle).boxSizing,Object.keys(f).forEach(function(e){c.style[e]=f[e]}),d(c),c.value=r,h=m(c,t),c.value=r,h=m(c,t),c.value="x",x=(b=c.scrollHeight-o)*n,"border-box"===p&&(x=x+o+u),h=Math.max(x,h),v=b*a,"border-box"===p&&(v=v+o+u),[h=Math.min(v,h),b]),w=S[0],O=S[1];R.current!==w&&(R.current=w,e.style.setProperty("height",w+"px","important"),y(w,{rowHeight:O}))}};return a.useLayoutEffect(T),b($,function(){if(!O){var e=$.current.value;requestAnimationFrame(function(){var t=$.current;t&&e!==t.value&&T()})}}),x(T),v(T),a.createElement("textarea",(0,r.f)({},w,{onChange:function(e){O||T(),p(e)},ref:j}))}),O=e.i(584984);let{spacing:$,colors:j,breakpoints:R,fontSize:E}=e.i(129704).U,T=t.U.form.withConfig({displayName:"styles__StyledSearchForm",componentId:"sc-a7afdf02-0"})`
  padding: ${e=>e.$isResultsPage?0:`${$.medium} ${$.small}`};
  background-color: ${j.white};

  color: ${j.grey8};

  @media screen and (min-width: ${R.large}) {
    padding: ${e=>e.$isResultsPage?0:`${$.xlarge} ${$.xlarge}`};
  }

  @media screen and (min-width: ${R.xlarge}) {
    padding: ${e=>e.$isResultsPage?0:` ${$.xxlarge} ${$.xxxlarge}`};
  }
`,_=t.U.div.withConfig({displayName:"styles__SearchFormWrapper",componentId:"sc-a7afdf02-1"})`
  margin: ${e=>e.$isResultsPage?0:`${$.xlarge} -${$.small} 0`};
  @media screen and (min-width: ${e=>e.theme.breakpoints.large}) {
    margin: ${e=>e.$isResultsPage?0:`${$.xlarge} -${$.xlarge} 0`};
  }

  @media screen and (min-width: ${e=>e.theme.breakpoints.xlarge}) {
    margin: ${e=>e.$isResultsPage?0:`${$.xlarge} -${$.xxxlarge} 0`};
  }
`,U=t.m`
  display: block;
  background: white;
  border-width: 1px 1px 2px;
  border-color: ${j.grey6};
  outline: none;
  font-size: ${E.small};
  padding: ${$.small} ${$.xlarge} ${$.small} ${$.small};
  line-height: 1.4em;
  width: 100%;
  color: inherit;
  border-radius: 0;

  &:hover,
  &:focus {
    border-color: ${e=>e.$hasError?j.error:j.grey8};
    border-width: 2px;
  }
  &::placeholder {
    color: ${j.grey6};
  }

  ${e=>e.$hasError&&t.m`
      border-color: ${j.error};
      border-width: 2px;
    `}
`,A=(0,t.U)(w).withConfig({displayName:"styles__TextArea",componentId:"sc-a7afdf02-2"})`
  ${U}
  min-height: 100%;
  resize: none;
`,L=t.U.p.attrs({role:"alert"}).withConfig({displayName:"styles__InputError",componentId:"sc-a7afdf02-3"})`
  color: ${j.error};
  font-size: ${E.small};
  margin-top: 0;
  margin-bottom: 0;
`,F=t.U.div.withConfig({displayName:"styles__FieldMeta",componentId:"sc-a7afdf02-4"})`
  display: flex;
  flex-flow: row wrap;
  align-items: flex-start;
  grid-row: 2;

  @media screen and (max-width: ${R.medium}) {
    order: 2;
  }
`;t.U.small.withConfig({displayName:"styles__FieldInfo",componentId:"sc-a7afdf02-5"})`
  font-size: ${E.small};
  margin-left: auto;
  color: ${e=>e.limitExceeded?j.error:"inherit"};
  flex-basis: 100%;
  order: -1;
  text-align: right;

  &:not(:first-child) {
    margin-bottom: ${$.xsmall};
  }

  @media screen and (min-width: ${R.small}) {
    font-size: ${E.xsmall};
    flex-basis: auto;
    order: 2;

    &:not(:first-child) {
      margin-bottom: 0;
    }
  }
`;let q=t.U.div.withConfig({displayName:"styles__StyledRadioButtonsWrapper",componentId:"sc-a7afdf02-6"})`
  margin-bottom: ${$.small};
  font-size: ${E.small};
  display: flex;
  align-items: self-start;
  gap: ${$.small};
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
    right: ${$.medium};
    top: 12px;
  }
`,N=t.U.div.withConfig({displayName:"styles__SearchBoxContainer",componentId:"sc-a7afdf02-8"})`
  display: grid;
  grid-template-columns: 3fr 1fr;
  grid-gap: ${$.small};
  @media screen and (max-width: ${R.medium}) {
    display: flex;
    flex-direction: column;
  }
`,M=t.U.label.withConfig({displayName:"styles__StyledRadioLabel",componentId:"sc-a7afdf02-9"})`
  display: flex;
`,I=t.U.input.withConfig({displayName:"styles__StyledRadioButton",componentId:"sc-a7afdf02-10"})`
  height: 20px;
  width: 20px;
  margin: 0 ${$.xsmall} 0 0;
  appearance: none;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 2px ${j.grey6};
  &:hover {
    box-shadow: 0 0 0 2px #000;
  }
  &:checked {
    background-color: ${j.linkBlue};
  }
`;e.s(["f",0,F,"H",0,L,"n",0,N,"P",0,_,"d",0,I,"S",0,q,"F",0,M,"J",0,T,"z",0,C,"p",0,A],913192);var z=e.i(33290);let k={search:{query:{minLength:5,minLengthLatin:3,maxLength:z.U?1500:5e3,label:"search query",required:!0}},"recommend-stem":{query:{minLength:36,minLengthLatin:36,maxLength:z.U?1500:5e3,label:"abstract",required:!0}}},D={query:void 0};e.s(["U",0,e=>{let[t,r]=(0,a.useState)(D),n=(0,a.useMemo)(()=>(({mode:e,fields:t})=>{let r={...D};return Object.entries(t).forEach(([t,n])=>{let{required:a,minLengthLatin:i,minLength:s,maxLength:l,label:o}=k[e][t],u=n.trim(),d=u.replaceAll(/\s/g,""),c=d.replaceAll(/[^a-z]+/gi,"");a&&!d?r[t]=`Please enter ${k[e][t].label}`:s&&d.length<s?r[t]=`Please enter a longer ${k[e][t].label}`:i&&c.length<i?r[t]=`Please enter a longer ${k[e][t].label}, including more latin characters.`:l&&u.length>l&&(r[t]=`Please reduce the length of your ${o}`)}),r})(e),[e]),i=(0,a.useMemo)(()=>Object.values(n).some(e=>void 0!==e),[n]),s=(0,a.useCallback)(e=>{e?r({...t,[e]:n[e]}):r(n)},[n,t]);return(0,a.useEffect)(()=>{let e=!1;Object.entries(t).forEach(([t,r])=>{r&&n[t]!==r&&(e=!0)}),e&&s()},[n,s,t]),{errors:t,showErrors:s,hasErrors:i}},"n",0,k],211768);var P=e.i(843476),J=e.i(672195),B=e.i(145617),H=e.i(343794);e.s(["f",0,({maxLength:e,length:t})=>{if(!e)return null;let r=t>e,n="";return r?n=` (${(0,J.f)(t-e)} too many)`:t>e-50&&(n=` (${(0,J.f)(e-t)} left)`),(0,P.jsx)("small",{className:(0,H.default)(B.default.fieldInfo,{[B.default.fieldInfoLimitExceeded]:r}),children:`Maximum ${(0,J.f)(e)} characters ${n}`})}],5383)},827933,e=>{var t=e.i(843476),r=e.i(271645),n=e.i(526732);e.i(843553);var a=e.i(291648),i=e.i(259209),s=e.i(627818);let l=(e,t=0)=>{"function"==typeof window.adobe?.target?.triggerView?window.adobe.target.triggerView(e):t<3&&setTimeout(()=>{l(e,t+1)},100)};var o=e.i(209711);e.s(["default",0,e=>{let{children:u,...d}=e,{data:c}=(0,n.U)(),m=(e=>{let{pageName:t,session:r}=e;switch(t){case s.f.JF_HOME:case s.f.JF_MY_JOURNALS:case s.f.JF_ABSTRACT_SEARCH_JOURNAL_LIST:case s.f.JF_METADATA_SEARCH_JOURNAL_LIST:return(0,a.j)(t,r);case s.f.RA_CONFIRM_TRANSFER:case s.f.RA_TRANSFER_STATUS:case s.f.RA_JOURNAL_LIST:case s.f.TT_CONFIRM_TRANSFER:case s.f.TT_TRANSFER_STATUS:case s.f.TT_JOURNAL_LIST:return(0,a.i)(e);default:return(0,a.h)({pageName:t,serviceName:e.serviceName,errorType:e.errorType,submissionData:e.submissionData,statusCode:e.statusCode})}})({...d,session:c});return(0,r.useEffect)(()=>{setTimeout(()=>{l(e.pageName),(0,i.J)("newPage",m)},0)},[e.pageName,m]),(0,t.jsx)("div",{className:o.default.pageTracker,children:u})}],827933)},672195,e=>{let t={number:{maximumFractionDigits:2},integer:{maximumFractionDigits:0},percentage:{style:"percent",maximumFractionDigits:0}};e.s(["f",0,(e,r="number",n={},a="en-US")=>{let i=e;return null==i||isNaN(i)?"—":"number"!=typeof i?i:("percentage"===r&&(i/=100),i.toLocaleString(a,{...t[r],...n}))}])},259209,e=>{let t=(e,t)=>{window.appData.push({event:e,...t})};e.s(["S",0,e=>"function"==typeof window?.s?.visitor?.appendVisitorIDsTo?window.s.visitor.appendVisitorIDsTo(e):e,"M",0,({action:e,status:r})=>{t("formError",{form:{errorType:`se-jf_${e}-${r}`}})},"x",0,e=>{window.appData.push({event:"buttonClick",buttonType:e})},"z",0,t,"J",0,(e,r)=>{"complete"===document.readyState?t(e,r):document.onreadystatechange=()=>{"complete"===document.readyState&&t(e,r)}}])},49321,e=>{var t=e.i(86049),r=e.i(947421),n=e.i(589271),a=e.i(618566),i=e.i(680902),s=e.i(622289),l=e.i(271645);function o(e,t,r){try{return e(t)}catch(e){return(0,s.l)("[nuqs] Error while parsing value `%s`: %O"+(r?" (for key `%s`)":""),t,e,r),null}}function u(e){function t(t){if(void 0===t)return null;let r="";if(Array.isArray(t)){if(void 0===t[0])return null;r=t[0]}return"string"==typeof t&&(r=t),o(e.parse,r)}return{type:"single",eq:(e,t)=>e===t,...e,parseServerSide:t,withDefault(e){return{...this,defaultValue:e,parseServerSide:r=>t(r)??e}},withOptions(e){return{...this,...e}}}}let d=u({parse:e=>e,serialize:String});u({parse:e=>{let t=parseInt(e);return t==t?t:null},serialize:e=>""+Math.round(e)}),u({parse:e=>{let t=parseInt(e);return t==t?t-1:null},serialize:e=>""+Math.round(e+1)}),u({parse:e=>{let t=parseInt(e,16);return t==t?t:null},serialize:e=>{let t=Math.round(e).toString(16);return(1&t.length?"0":"")+t}}),u({parse:e=>{let t=parseFloat(e);return t==t?t:null},serialize:String});let c=u({parse:e=>"true"===e.toLowerCase(),serialize:String});function m(e,t){return e.valueOf()===t.valueOf()}function f(e){return u({parse:t=>e.includes(t)?t:null,serialize:String})}u({parse:e=>{let t=parseInt(e);return t==t?new Date(t):null},serialize:e=>""+e.valueOf(),eq:m}),u({parse:e=>{let t=new Date(e);return t.valueOf()==t.valueOf()?t:null},serialize:e=>e.toISOString(),eq:m}),u({parse:e=>{let t=new Date(e.slice(0,10));return t.valueOf()==t.valueOf()?t:null},serialize:e=>e.toISOString().slice(0,10),eq:m});let p=(0,i.r)(),h={};function g(e,t,r,n,a,s){let l=!1,u=Object.entries(e).reduce((e,[u,d])=>{var c;let m=t?.[u]??u,f=n[m],p="multi"===d.type?[]:null,h=void 0===f?("multi"===d.type?r?.getAll(m):r?.get(m))??p:f;return a&&s&&((c=a[m]??p)===h||null!==c&&null!==h&&"string"!=typeof c&&"string"!=typeof h&&c.length===h.length&&c.every((e,t)=>e===h[t]))?e[u]=s[u]??null:(l=!0,e[u]=((0,i.i)(h)?null:o(d.parse,h,m))??null,a&&(a[m]=h)),e},{});if(!l){let t=Object.keys(e),r=Object.keys(s??{});l=t.length!==r.length||t.some(e=>!r.includes(e))}return{state:u,hasChanged:l}}function y(e,t){return Object.fromEntries(Object.keys(e).map(r=>[r,e[r]??t[r]??null]))}let b=(e,t)=>({defaultValue:e,parse:t}),x=(e,r)=>b(e,e=>{let n,{min:a,max:i}=t.y[r];return"string"==typeof e?!isNaN(n=parseInt(e))&&n>=a&&n<=i?n:null:null});e.s(["f",0,()=>{let e=(0,a.useSearchParams)(),{affiliations:t}=(0,r.useAffiliations)(),o=e.get("query")??"",u=e.get("paperAbstract")??"",m="string"==typeof o&&o.length>0?o:"string"==typeof u?u:"",v=t?.authorOrg?t.authorOrg.id:"",[S,w]=function(e,t={}){let r=(0,l.useId)(),n=(0,s.i)(),a=(0,s.a)(),{history:o="replace",scroll:u=n?.scroll??!1,shallow:d=n?.shallow??!0,throttleMs:c=i.s.timeMs,limitUrlUpdates:m=n?.limitUrlUpdates,clearOnDefault:f=n?.clearOnDefault??!0,startTransition:b,urlKeys:x=h}=t,v=Object.keys(e).join(","),S=(0,l.useMemo)(()=>Object.fromEntries(Object.keys(e).map(e=>[e,x[e]??e])),[v,JSON.stringify(x)]),w=(0,s.r)(Object.values(S)),O=w.searchParams,$=(0,l.useRef)({}),j=(0,l.useMemo)(()=>Object.fromEntries(Object.keys(e).map(t=>[t,e[t].defaultValue??null])),[Object.values(e).map(({defaultValue:e})=>e).join(",")]),R=i.t.useQueuedQueries(Object.values(S)),[E,T]=(0,l.useState)(()=>g(e,x,O??new URLSearchParams,R).state),_=(0,l.useRef)(E);if((0,s.c)("[nuq+ %s `%s`] render - state: %O, iSP: %s",r,v,E,O),Object.keys($.current).join("&")!==Object.values(S).join("&")){let{state:t,hasChanged:n}=g(e,x,O,R,$.current,_.current);n&&((0,s.c)("[nuq+ %s `%s`] State changed: %O",r,v,{state:t,initialSearchParams:O,queuedQueries:R,queryRef:$.current,stateRef:_.current}),_.current=t,T(t)),$.current=Object.fromEntries(Object.entries(S).map(([t,r])=>[r,e[t]?.type==="multi"?O?.getAll(r):O?.get(r)??null]))}(0,l.useEffect)(()=>{let{state:t,hasChanged:n}=g(e,x,O,R,$.current,_.current);n&&((0,s.c)("[nuq+ %s `%s`] State changed: %O",r,v,{state:t,initialSearchParams:O,queuedQueries:R,queryRef:$.current,stateRef:_.current}),_.current=t,T(t))},[Object.values(S).map(e=>`${e}=${O?.getAll(e)}`).join("&"),JSON.stringify(R)]),(0,l.useEffect)(()=>{let t=Object.keys(e).reduce((t,n)=>(t[n]=({state:t,query:a})=>{T(i=>{let{defaultValue:l}=e[n],o=S[n],u=t??l??null;return Object.is(i[n]??l??null,u)?((0,s.c)("[nuq+ %s `%s`] Cross-hook key sync %s: %O (default: %O). no change, skipping, resolved: %O",r,v,o,t,l,_.current),i):(_.current={..._.current,[n]:u},$.current[o]=a,(0,s.c)("[nuq+ %s `%s`] Cross-hook key sync %s: %O (default: %O). updateInternalState, resolved: %O",r,v,o,t,l,_.current),_.current)})},t),{});for(let n of Object.keys(e)){let e=S[n];(0,s.c)("[nuq+ %s `%s`] Subscribing to sync for `%s`",r,e,v),p.on(e,t[n])}return()=>{for(let n of Object.keys(e)){let e=S[n];(0,s.c)("[nuq+ %s `%s`] Unsubscribing to sync for `%s`",r,e,v),p.off(e,t[n])}}},[v,S]);let U=(0,l.useCallback)((t,n={})=>{let l,h=Object.fromEntries(Object.keys(e).map(e=>[e,null])),g="function"==typeof t?t(y(_.current,j))??h:t??h;(0,s.c)("[nuq+ %s `%s`] setState: %O",r,v,g);let x=0,O=!1,$=[];for(let[t,r]of Object.entries(g)){let h=e[t],g=S[t];if(!h||void 0===r)continue;(n.clearOnDefault??h.clearOnDefault??f)&&null!==r&&void 0!==h.defaultValue&&(h.eq??((e,t)=>e===t))(r,h.defaultValue)&&(r=null);let y=null===r?null:(h.serialize??String)(r);p.emit(g,{state:r,query:y});let v={key:g,query:y,options:{history:n.history??h.history??o,shallow:n.shallow??h.shallow??d,scroll:n.scroll??h.scroll??u,startTransition:n.startTransition??h.startTransition??b}};if(n?.limitUrlUpdates?.method==="debounce"||m?.method==="debounce"||h.limitUrlUpdates?.method==="debounce"){!0===v.options.shallow&&console.warn((0,s.s)(422));let e=n?.limitUrlUpdates?.timeMs??m?.timeMs??h.limitUrlUpdates?.timeMs??i.s.timeMs,t=i.t.push(v,e,w,a);x<e&&(l=t,x=e)}else{let e=n?.limitUrlUpdates?.timeMs??h?.limitUrlUpdates?.timeMs??m?.timeMs??n.throttleMs??h.throttleMs??c;$.push(i.t.abort(g)),i.n.push(v,e),O=!0}}let R=$.reduce((e,t)=>t(e),O?i.n.flush(w,a):i.n.getPendingPromise(w));return l??R},[v,o,d,u,c,m?.method,m?.timeMs,b,S,w.updateUrl,w.getSearchParamsSnapshot,w.rateLimitFactor,a,j]);return[(0,l.useMemo)(()=>y(E,j),[E,j]),U]}({citeScoreGte:x(null,"citeScore"),citeScoreLt:x(null,"citeScore"),impactFactorGte:x(null,"impactFactor"),impactFactorLt:x(null,"impactFactor"),timeToFirstDecisionLt:x(null,"timeToFirstDecision"),timeToAcceptanceLt:x(null,"timeToAcceptance"),goldOpenAccess:c.withDefault(!0),subscription:c.withDefault(!0),sortBy:f(Object.values(n.b)).withDefault(n.b.Default),sortOrder:f(Object.values(n.f)).withDefault(n.f.Ascending),query:d.withDefault(m),mode:b(n.l.RECOMMEND_STEM,e=>e),ecrId:d.withDefault(v),agreementsFilter:f(Object.values(n.R)).withDefault(n.R.ALL_JOURNALS)},{history:"push",clearOnDefault:!1});return[S,w]}],49321)}],145617,e=>{e.v({fieldInfo:"iVXSQq_fieldInfo",fieldInfoLimitExceeded:"iVXSQq_fieldInfoLimitExceeded"})},553686,e=>{e.v({button:"KdGCSW_button"})},209711,e=>{e.v({pageTracker:"Q0Elea_pageTracker"})}]);