(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["object"==typeof document?document.currentScript:void 0,[680902,622289,e=>{var t=e.i(247167),r=e.i(271645);let n=function(){if("u"<typeof window)return(t.default.env.DEBUG||"").includes("nuqs");try{let e="nuqs-localStorage-test";if("u"<typeof localStorage)return!1;localStorage.setItem(e,e);let t=localStorage.getItem(e)===e;return localStorage.removeItem(e),t&&(localStorage.getItem("debug")||"").includes("nuqs")}catch{return!1}}();function o(e,...t){if(!n)return;let r=function(e,...t){return e.replace(/%[sfdO]/g,e=>{let r=t.shift();return"%O"===e&&r?JSON.stringify(r).replace(/"([^"]+)":/g,"$1:"):String(r)})}(e,...t);performance.mark(r);try{console.log(e,...t)}catch{console.log(r)}}let i={303:"Multiple adapter contexts detected. This might happen in monorepos.",404:"nuqs requires an adapter to work with your framework.",409:"Multiple versions of the library are loaded. This may lead to unexpected behavior. Currently using `%s`, but `%s` (via the %s adapter) was about to load on top.",414:"Max safe URL length exceeded. Some browsers may not be able to accept this URL. Consider limiting the amount of state stored in the URL.",422:"Invalid options combination: `limitUrlUpdates: debounce` should be used in SSR scenarios, with `shallow: false`",429:"URL update rate-limited by the browser. Consider increasing `throttleMs` for key(s) `%s`. %O",500:"Empty search params cache. Search params can't be accessed in Layouts.",501:"Search params cache already populated. Have you called `parse` twice?"};function s(e){return`[nuqs] ${i[e]}
  See https://nuqs.dev/NUQS-${e}`}let a=(0,r.createContext)({useAdapter(){throw Error(s(404))}});function l(e){return{method:"throttle",timeMs:e}}a.displayName="NuqsAdapterContext",n&&"u">typeof window&&(window.__NuqsAdapterContext&&window.__NuqsAdapterContext!==a&&console.error(s(303)),window.__NuqsAdapterContext=a),e.s(["a",0,()=>(0,r.useContext)(a).processUrlSearchParams,"c",0,o,"i",0,()=>(0,r.useContext)(a).defaultOptions,"l",0,function(e,...t){n&&console.warn(e,...t)},"n",0,function(e){return({children:t,defaultOptions:n,processUrlSearchParams:o,...i})=>(0,r.createElement)(a.Provider,{...i,value:{useAdapter:e,defaultOptions:n,processUrlSearchParams:o}},t)},"o",0,function(e){if(0===e.size)return"";let t=[];for(let[r,n]of e.entries()){let e=r.replace(/#/g,"%23").replace(/&/g,"%26").replace(/\+/g,"%2B").replace(/=/g,"%3D").replace(/\?/g,"%3F");t.push(`${e}=${n.replace(/%/g,"%25").replace(/\+/g,"%2B").replace(/ /g,"+").replace(/#/g,"%23").replace(/&/g,"%26").replace(/"/g,"%22").replace(/'/g,"%27").replace(/`/g,"%60").replace(/</g,"%3C").replace(/>/g,"%3E").replace(/[\x00-\x1F]/g,e=>encodeURIComponent(e))}`)}return"?"+t.join("&")},"r",0,function(e){let t=(0,r.useContext)(a);if(!("useAdapter"in t))throw Error(s(404));return t.useAdapter(e)},"s",0,s],622289);let u=l(function(){if("u"<typeof window||!window.GestureEvent)return 50;try{let e=navigator.userAgent?.match(/version\/([\d\.]+) safari/i);return parseFloat(e[1])>=17?120:320}catch{return 320}}());function c(e,t,r){if("string"==typeof e)r.set(t,e);else{for(let n of(r.delete(t),e))r.append(t,n);r.has(t)||r.set(t,"")}return r}function d(){let e=new Map;return{on(t,r){let n=e.get(t)||[];return n.push(r),e.set(t,n),()=>this.off(t,r)},off(t,r){let n=e.get(t);n&&e.set(t,n.filter(e=>e!==r))},emit(t,r){e.get(t)?.forEach(e=>e(r))}}}function h(e,t,r){let n=setTimeout(function(){e(),r.removeEventListener("abort",o)},t);function o(){clearTimeout(n),r.removeEventListener("abort",o)}r.addEventListener("abort",o)}function p(){let e=Promise;if(Promise.hasOwnProperty("withResolvers"))return Promise.withResolvers();let t=()=>{},r=()=>{};return{promise:new e((e,n)=>{t=e,r=n}),resolve:t,reject:r}}function m(){return new URLSearchParams(location.search)}var f=class{updateMap=new Map;options={history:"replace",scroll:!1,shallow:!0};timeMs=u.timeMs;transitions=new Set;resolvers=null;controller=null;lastFlushedAt=0;resetQueueOnNextPush=!1;push({key:e,query:t,options:r},n=u.timeMs){this.resetQueueOnNextPush&&(this.reset(),this.resetQueueOnNextPush=!1),o("[nuqs gtq] Enqueueing %s=%s %O",e,t,r),this.updateMap.set(e,t),"push"===r.history&&(this.options.history="push"),r.scroll&&(this.options.scroll=!0),!1===r.shallow&&(this.options.shallow=!1),r.startTransition&&this.transitions.add(r.startTransition),(!Number.isFinite(this.timeMs)||n>this.timeMs)&&(this.timeMs=n)}getQueuedQuery(e){return this.updateMap.get(e)}getPendingPromise({getSearchParamsSnapshot:e=m}){return this.resolvers?.promise??Promise.resolve(e())}flush({getSearchParamsSnapshot:e=m,rateLimitFactor:t=1,...r},n){if(this.controller??=new AbortController,!Number.isFinite(this.timeMs))return o("[nuqs gtq] Skipping flush due to throttleMs=Infinity"),Promise.resolve(e());if(this.resolvers)return this.resolvers.promise;this.resolvers=p();let i=()=>{this.lastFlushedAt=performance.now();let[t,o]=this.applyPendingUpdates({...r,autoResetQueueOnUpdate:r.autoResetQueueOnUpdate??!0,getSearchParamsSnapshot:e},n);null===o?(this.resolvers.resolve(t),this.resetQueueOnNextPush=!0):this.resolvers.reject(t),this.resolvers=null},s=()=>{let e=performance.now()-this.lastFlushedAt,r=this.timeMs,n=t*Math.max(0,r-e);o("[nuqs gtq] Scheduling flush in %f ms. Throttled at %f ms (x%f)",n,r,t),0===n?i():h(i,n,this.controller.signal)};return h(s,0,this.controller.signal),this.resolvers.promise}abort(){return this.controller?.abort(),this.controller=new AbortController,this.resolvers?.resolve(new URLSearchParams),this.resolvers=null,this.reset()}reset(){let e=Array.from(this.updateMap.keys());return o("[nuqs gtq] Resetting queue %s",JSON.stringify(Object.fromEntries(this.updateMap))),this.updateMap.clear(),this.transitions.clear(),this.options={history:"replace",scroll:!1,shallow:!0},this.timeMs=u.timeMs,e}applyPendingUpdates(e,t){let{updateUrl:r,getSearchParamsSnapshot:n}=e,i=n();if(o("[nuqs gtq] Applying %d pending update(s) on top of %s",this.updateMap.size,i.toString()),0===this.updateMap.size)return[i,null];let a=Array.from(this.updateMap.entries()),l={...this.options},u=Array.from(this.transitions);for(let[t,r]of(e.autoResetQueueOnUpdate&&this.reset(),o("[nuqs gtq] Flushing queue %O with options %O",a,l),a))null===r?i.delete(t):i=c(r,t,i);t&&(i=t(i));try{return!function(e,t){let r=t;for(let t=e.length-1;t>=0;t--){let n=e[t];if(!n)continue;let o=r;r=()=>n(o)}r()}(u,()=>{r(i,l)}),[i,null]}catch(e){return console.error(s(429),a.map(([e])=>e).join(),e),[i,e]}}};let g=new f;var y=class{callback;resolvers=p();controller=new AbortController;queuedValue=void 0;constructor(e){this.callback=e}abort(){this.controller.abort(),this.queuedValue=void 0}push(e,t){return this.queuedValue=e,this.controller.abort(),this.controller=new AbortController,h(()=>{let t=this.resolvers;try{o("[nuqs dq] Flushing debounce queue",e);let r=this.callback(e);o("[nuqs dq] Reset debounce queue %O",this.queuedValue),this.queuedValue=void 0,this.resolvers=p(),r.then(e=>t.resolve(e)).catch(e=>t.reject(e))}catch(e){this.queuedValue=void 0,t.reject(e)}},t,this.controller.signal),this.resolvers.promise}};let b=new class{throttleQueue;queues=new Map;queuedQuerySync=d();constructor(e=new f){this.throttleQueue=e}useQueuedQueries(e){var t,n;let o,i;return t=(e,t)=>this.queuedQuerySync.on(e,t),n=e=>this.getQueuedQuery(e),o=(0,r.useCallback)(()=>{let t=Object.fromEntries(e.map(e=>[e,n(e)]));return[JSON.stringify(t),t]},[e.join(","),n]),null===(i=(0,r.useRef)(null)).current&&(i.current=o()),(0,r.useSyncExternalStore)((0,r.useCallback)(r=>{let n=e.map(e=>t(e,r));return()=>n.forEach(e=>e())},[e.join(","),t]),()=>{let[e,t]=o();return i.current[0]===e?i.current[1]:(i.current=[e,t],t)},()=>i.current[1])}push(e,t,r,n){if(!Number.isFinite(t))return Promise.resolve((r.getSearchParamsSnapshot??m)());let i=e.key;if(!this.queues.has(i)){o("[nuqs dqc] Creating debounce queue for `%s`",i);let e=new y(e=>(this.throttleQueue.push(e),this.throttleQueue.flush(r,n).finally(()=>{this.queues.get(e.key)?.queuedValue===void 0&&(o("[nuqs dqc] Cleaning up empty queue for `%s`",e.key),this.queues.delete(e.key)),this.queuedQuerySync.emit(e.key)})));this.queues.set(i,e)}o("[nuqs dqc] Enqueueing debounce update %O",e);let s=this.queues.get(i).push(e,t);return this.queuedQuerySync.emit(i),s}abort(e){let t=this.queues.get(e);return t?(o("[nuqs dqc] Aborting debounce queue %s=%s",e,t.queuedValue?.query),this.queues.delete(e),t.abort(),this.queuedQuerySync.emit(e),e=>(e.then(t.resolvers.resolve,t.resolvers.reject),e)):e=>e}abortAll(){for(let[e,t]of this.queues.entries())o("[nuqs dqc] Aborting debounce queue %s=%s",e,t.queuedValue?.query),t.abort(),t.resolvers.resolve(new URLSearchParams),this.queuedQuerySync.emit(e);this.queues.clear()}getQueuedQuery(e){let t=this.queues.get(e)?.queuedValue?.query;return void 0!==t?t:this.throttleQueue.getQueuedQuery(e)}}(g);e.s(["a",0,c,"c",0,l,"i",0,function(e){return null===e||Array.isArray(e)&&0===e.length},"n",0,g,"o",0,function(e){return{method:"debounce",timeMs:e}},"r",0,d,"s",0,u,"t",0,b],680902)},865156,(e,t,r)=>{var n=e.r(232189);function o(){}function i(){}i.resetWarningCache=o,t.exports=function(){function e(e,t,r,o,i,s){if(s!==n){var a=Error("Calling PropTypes validators directly is not supported by the `prop-types` package. Use PropTypes.checkPropTypes() to call them. Read more at http://fb.me/use-check-prop-types");throw a.name="Invariant Violation",a}}function t(){return e}e.isRequired=e;var r={array:e,bigint:e,bool:e,func:e,number:e,object:e,string:e,symbol:e,any:e,arrayOf:t,element:e,elementType:e,instanceOf:t,node:e,objectOf:t,oneOf:t,oneOfType:t,shape:t,exact:t,checkPropTypes:i,resetWarningCache:o};return r.PropTypes=r,r}},232189,(e,t,r)=>{t.exports="SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED"},271070,e=>{var t=e.i(843476);let r=()=>(0,t.jsxs)("svg",{width:"94",height:"80",viewBox:"0 0 94 80",xmlns:"http://www.w3.org/2000/svg",children:[(0,t.jsx)("title",{children:"Failed icon"}),(0,t.jsx)("path",{d:"M19 36.462l2.039-2.04a1.442 1.442 0 0 1 2.039 2.04l-2.04 2.038 2.04 2.04a1.442 1.442 0 0 1-2.04 2.038L19 40.54l-2.039 2.04a1.442 1.442 0 0 1-2.039-2.04l2.039-2.039-2.039-2.038a1.442 1.442 0 0 1 2.039-2.04L19 36.463zm20 0l2.039-2.04a1.442 1.442 0 0 1 2.039 2.04l-2.04 2.038 2.04 2.04a1.442 1.442 0 0 1-2.04 2.038L39 40.54l-2.039 2.04a1.442 1.442 0 0 1-2.039-2.04l2.039-2.039-2.039-2.038a1.442 1.442 0 0 1 2.039-2.04L39 36.463zm37.45 17.025a1.5 1.5 0 0 1-1.5-1.5 8.499 8.499 0 0 0-7.666-8.459 1.502 1.502 0 0 1-1.35-1.639 1.508 1.508 0 0 1 1.638-1.348c5.461.53 9.803 4.88 10.324 10.342.035.363.053.731.053 1.104a1.5 1.5 0 0 1-1.5 1.5zM93.56 75.44A1.502 1.502 0 0 1 92.5 78c-.384 0-.768-.146-1.061-.439l-12.83-12.829A17.904 17.904 0 0 1 67 69c-9.924 0-18-8.075-18-18s8.076-18 18-18c9.926 0 18 8.075 18 18 0 4.424-1.61 8.474-4.268 11.611L93.56 75.44zM52 51c0 8.271 6.729 15 15 15 8.27 0 15-6.729 15-15 0-8.27-6.73-15-15-15-8.271 0-15 6.73-15 15zM10.5 11a1.5 1.5 0 1 1 0-3h46a1.5 1.5 0 0 1 0 3h-46zM54 16h4a2 2 0 0 1 2 2v12.5a1.5 1.5 0 1 1-3 0V19H10.5c-3.175 0-5.718-.845-7.5-2.434V70a7 7 0 0 0 7 7h47v-5.5a1.5 1.5 0 0 1 3 0V78a2 2 0 0 1-2 2H10C4.477 80 0 75.523 0 70V9.493C.004 4.055 4.131 0 10.022 0H56.5a1.5 1.5 0 0 1 0 3H10.022C5.855 3 3.108 5.622 3.003 9.282c.022.972.158 1.84.408 2.601.671 1.812 2.131 3.171 4.147 3.773.86.23 1.841.344 2.942.344H54zM35.999 60.5c-.315 0-.633-.099-.903-.303a8.402 8.402 0 0 0-5.108-1.697 8.406 8.406 0 0 0-5.088 1.683 1.499 1.499 0 0 1-2.099-.3 1.498 1.498 0 0 1 .299-2.1 11.385 11.385 0 0 1 6.888-2.283c2.531 0 4.922.796 6.916 2.303a1.5 1.5 0 0 1-.905 2.697z",fill:"#B9B9B9",fillRule:"nonzero"})]});var n=e.i(627818),o=e.i(260111),i=e.i(343794),s=e.i(376545),a=e.i(825743);e.s(["f",0,({className:e,hasMargin:l=!0,hasMaxWidth:u=!0,title:c="Something went wrong",customText:d,hasTitle:h=!0,icon:p=(0,t.jsx)(r,{})})=>(0,t.jsx)("div",{className:(0,i.default)(o.default.container,{[o.default["container--spaced"]]:l,[o.default["container--narrow"]]:u},e),"data-testid":"errordisplay","data-aa-region":n.d.ERROR_CARD,children:(0,t.jsxs)("div",{className:o.default.content,children:[h&&(0,t.jsx)(a.f,{as:"h1",fontWeight:700,fontSize:40,children:c}),d||(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)("p",{children:"We're sorry, Journal Finder failed to load."}),(0,t.jsx)("p",{children:"Please refresh the page to try again."}),(0,t.jsx)("p",{children:(0,t.jsx)(s.f,{iconLeft:"refresh",onClick:()=>window.location.reload(),variant:"primary",size:"large",label:"Refresh page"})})]}),(0,t.jsx)("div",{className:o.default.iconWrapper,children:p})]})})],271070)},460041,435826,e=>{var t=e.i(843476),r=e.i(326472),n=e.i(997053),o=e.i(129704);let i=n.U.span.withConfig({displayName:"PendoFeedbackButton.styles__StyledInlineWrapper",componentId:"sc-1e5e9964-0"})`
  position: relative;
`,s=n.U.div.withConfig({displayName:"PendoFeedbackButton.styles__StyledGreyFill",componentId:"sc-1e5e9964-1"})`
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  background: ${e=>e.theme.colors.grey1};
`,a=n.U.div.withConfig({displayName:"PendoFeedbackButton.styles__StyledStickyButtonContainer",componentId:"sc-1e5e9964-2"})`
  display: flex;
  justify-content: flex-end;
  position: sticky;
  bottom: 0;
  z-index: 10;
  min-height: ${e=>e.theme.spacing.xxxlarge};
  pointer-events: none;

  @media screen and (max-width: ${o.e.small}) {
    justify-content: center;

    &[data-pendo-page="pendo-home-page"] {
      position: static;
    }
  }

  // Override styles from Pendo-injected Button
  ._pendo-badge {
    pointer-events: all;
    cursor: pointer !important;
    margin: ${e=>e.theme.spacing.small} ${e=>e.theme.spacing.small}
      ${e=>e.theme.spacing.small} 0 !important;
    display: inline-flex !important;
    gap: ${e=>e.theme.spacing.small} !important;
    align-items: center !important;
    padding: calc(
        ${e=>e.theme.spacing.xxsmall} + ${e=>e.theme.spacing.xsmall}
      )
      ${e=>e.theme.spacing.small} !important;
    border: 2px solid ${e=>e.theme.colors.tertiaryYellow2} !important;
    border-radius: 2px !important;
    font-size: inherit !important;
    line-height: inherit !important;
    white-space: nowrap !important;
    text-decoration: none !important;
    background-color: ${e=>e.theme.colors.tertiaryYellow2} !important;
    color: black !important;
    transition: all 0.2s !important;
    &:after {
      content: url(/images/icons/send.svg);
      min-width: auto !important;
      height: ${e=>e.theme.fontSize.small} !important;
      margin-top: -2px !important;
      background: url(/images/icons/send-hover.svg) no-repeat -100px -100px;
    }
    &:hover {
      background-color: white !important;
      border-color: ${e=>e.theme.colors.orange} !important;
      color: black !important;
      &:after {
        content: url(/images/icons/send-hover.svg);
      }
    }
    &:focus {
      outline: 0 !important;
      box-shadow:
        0 0 0 2px white,
        0 0 0 4px ${e=>e.theme.colors.orange} !important;
    }
    &:focus:hover {
      box-shadow: none !important;
    }
    ._pendo-badge-text {
      font-size: inherit !important;
      color: inherit !important;
    }

    @media screen and (max-width: ${o.e.small}) {
      margin-right: 0 !important;
    }
  }
`;var l=e.i(627818);e.s(["f",0,()=>{let e=(0,r.f)(),n=e&&["404","results"].includes(e);return(0,t.jsxs)(i,{children:[n&&(0,t.jsx)(s,{}),(0,t.jsx)(a,{"data-pendo-page":`pendo-${e}-page`,"data-pendo-id":"floating-feedback","data-aa-region":l.d.MARKETING_CARD,children:" "})]})}],460041);var u=e.i(584984);let c=n.m`
  font-family: ${o.j.primary};
  font-variant: common-ligatures lining-nums contextual;
  font-variant-numeric: lining-nums proportional-nums;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;

  a {
    text-decoration-skip: edges;
  }
`,d=n.m`
  img {
    height: auto;
    max-width: 100%;
  }

  p {
    &:first-child {
      margin-top: 0;
    }
    &:last-child {
      margin-bottom: 0;
    }
  }

  svg {
    flex-shrink: 0;
  }
`,h=n.m`
  margin: 0;
  color: ${o.n.grey8};
  -ms-overflow-style: scrollbar;
  line-height: 1.4;
  font-size: 1.125em;
  box-sizing: border-box;
  -webkit-text-size-adjust: 100%;

  *,
  *::before,
  *::after {
    box-sizing: inherit;
  }

  ${c};
  ${d};

  @media screen and (min-width: ${o.e.medium}) {
    font-size: 1.25em;
  }
`,p=n.m`
  h1,
  h2 {
    font-weight: bold;
    font-family: ${o.j.primary};
    color: inherit;
    line-height: 1.334;
    margin-top: 0.5em;
    margin-bottom: 0.5em;
  }

  h1 {
    font-size: 1.6em;
  }

  h2 {
    font-size: ${o.J.large};
  }

  @media screen and (min-width: ${o.e.small}) {
    h1 {
      font-size: 2em;
    }
    h2 {
      font-size: 1.5em;
    }
  }
`,m=n.Q`
  /** Add overflow hidden to both the HTML and BODY element otherwise you will still be able to scroll on iOS */
  .settings-modal-open {
    &,
    body {
      overflow: hidden;
      position: relative;
      height: 100%;
    }
  }

  .ReactModal__Body--open {
    overflow: hidden !important;
    position: relative !important;
    padding-left: 0px;
    padding-top: 0px;
    padding-right: 0px;
    margin-left: 0;
    margin-top: 0;
  }

  body {
    ${h};
  }

  /** Override form components font */
  button,
  textarea,
  input {
    ${c};
  }

  #main {
    overflow: hidden;
  }

  /** Reset global header font size */
  #gh-cnt button,
  #gh-cnt input,
  #gh-cnt optgroup,
  #gh-cnt select,
  #gh-cnt textarea {
    font-size: 100%;
  }

  /** Override global header font */
  #gh-cnt * {
    ${c}
  }

  /** IE11 by default shifts button children when focussing, See: https://stackoverflow.com/questions/10305658/prevent-button-from-shifting-during-click-in-ie  */
  button > * {
    position: relative;
  }

  ${u.U.ie11Blocks};
  ${p};

  @media screen and (min-width: ${o.U.breakpoints.small}){
    .settings-modal-open {
      &,
      body {
        overflow: visible;
        position: static;
        height: auto;
      }
    }
  }

  a:focus-visible,
  button:focus-visible {
    ${u.U.focusRing}
  }
`;e.s(["f",0,m],435826)},33290,e=>{let t=(0,e.i(488381).default)(),r=!!window.MSInputMethodContext&&!!document.documentMode;e.s(["U",0,r,"_",0,()=>t&&t<11])},326472,e=>{var t=e.i(618566);e.s(["f",0,()=>{let e=(0,t.usePathname)();return"string"==typeof e?e.replace("/","").replace(/\//g,":")||"home":void 0}])},584984,e=>{var t=e.i(997053),r=e.i(129704);let n=t.m`
  width: 100%;
  padding-left: ${r.O.small};
  padding-right: ${r.O.small};
  margin-left: auto;
  margin-right: auto;

  @media screen and (min-width: ${r.e.large}) {
    max-width: 48em;
    padding-left: 0;
    padding-right: 0;
  }
`,o=t.m`
  font-size: ${r.J.xsmall};
  color: ${r.n.grey6};
  line-height: 1.6;
  margin-bottom: ${r.O.xxsmall};
`,i=t.m`
  /** Add the correct display in browsers that don't support HTML5 elements by default. */
  article,
  aside,
  footer,
  header,
  nav,
  figcaption,
  figure,
  main,
  section {
    display: block;
  }
`,s=t.m`
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  border: 0;
  margin: 0;
  padding: 0;
  -webkit-appearance: none;
  -moz-appearance: none;
  flex-shrink: 0;
  white-space: nowrap;
  text-decoration: none;
  background: none;
  color: inherit;
  cursor: pointer;
`,a=t.m`
  ${s};
  display: block;
  font-size: ${r.J.small};
  color: ${r.n.blue};
  transition: ${(0,r.$)()};
  outline: none;
  box-shadow: 0 1px 0 0 transparent;

  &:hover,
  &:active,
  &:focus {
    box-shadow: 0 1px 0 0 ${r.n.grey4};
  }

  svg {
    width: 1em;
    height: 0.6em;
    margin-left: ${r.O.xsmall};
    transition: ${(0,r.$)("transform")};
    transform: ${e=>e.isExpanded?"rotate(180deg)":"none"};
  }
`,l=t.m`
  font-family: ${r.j.primary};
  font-size: 1.6em;
  margin-top: 0;
  margin-bottom: ${r.O.medium};

  @media screen and (min-width: ${r.e.small}) {
    font-size: 2em;
  }
`,u=t.m`
  outline-color: ${r.n.orange};
  outline-offset: 1px;
  outline-style: solid;
  outline-width: 2px;
`;e.s(["n",0,s,"U",0,{maxWidth:n,definitionLabel:o,buttonReset:s,ie11Blocks:i,errorTitle:l,toggleButton:a,focusRing:u},"a",0,u])}],343794,(e,t,r)=>{!function(){"use strict";var r={}.hasOwnProperty;function n(){for(var e="",t=0;t<arguments.length;t++){var i=arguments[t];i&&(e=o(e,function(e){if("string"==typeof e||"number"==typeof e)return e;if("object"!=typeof e)return"";if(Array.isArray(e))return n.apply(null,e);if(e.toString!==Object.prototype.toString&&!e.toString.toString().includes("[native code]"))return e.toString();var t="";for(var i in e)r.call(e,i)&&e[i]&&(t=o(t,i));return t}(i)))}return e}function o(e,t){return t?e?e+" "+t:e+t:e}if(t.exports)n.default=n,t.exports=n;else if("function"==typeof define&&"object"==typeof define.amd&&define.amd)void 0!==n&&e.v(n);else window.classNames=n}()},488381,(e,t,r)=>{t.exports=function(){var e=window.navigator.userAgent,t=e.indexOf("MSIE ");if(t>0)return parseInt(e.substring(t+5,e.indexOf(".",t)),10);if(e.indexOf("Trident/")>0){var r=e.indexOf("rv:");return parseInt(e.substring(r+3,e.indexOf(".",r)),10)}var n=e.indexOf("Edge/");return n>0&&parseInt(e.substring(n+5,e.indexOf(".",n)),10)}},745009,(e,t,r)=>{e.i(247167),t.exports=e.r(865156)()},260111,e=>{e.v({container:"QBUpTa_container","container-narrow":"QBUpTa_container-narrow","container-spaced":"QBUpTa_container-spaced",content:"QBUpTa_content",iconWrapper:"QBUpTa_iconWrapper"})}]);