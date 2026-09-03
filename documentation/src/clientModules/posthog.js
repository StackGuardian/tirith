/**
 * Loads PostHog, and only if a key was supplied at build time.
 *
 * The key is read from siteConfig.customFields, which docusaurus.config.js
 * fills from the POSTHOG_KEY environment variable. Nothing is committed: an
 * unconfigured build -- a local `docusaurus start`, a fork, a contributor's
 * checkout -- ships no tracking script at all, and src/lib/analytics.js
 * degrades to a no-op on its own.
 */

import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';
import siteConfig from '@generated/docusaurus.config';

if (ExecutionEnvironment.canUseDOM) {
  const {posthogKey, posthogHost} = siteConfig.customFields || {};

  if (posthogKey) {
    // The official snippet, transcribed rather than depended on, so the docs
    // build does not grow a package for eight events.
    /* eslint-disable */
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys onSessionId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    /* eslint-enable */

    window.posthog.init(posthogKey, {
      api_host: posthogHost || 'https://eu.i.posthog.com',

      // A public documentation page has no business recording what a visitor
      // types, and the landing page's forms and code blocks would be exactly
      // what got recorded.
      autocapture: false,
      disable_session_recording: true,

      // Surveys can open a dialog over the page. Nothing here asks for one.
      disable_surveys: true,

      /*
       * COOKIELESS. This was `localStorage+cookie`, which is what makes a
       * consent banner necessary in the EU: a cookie set for analytics is not
       * strictly necessary to deliver the page, and this site has no banner and
       * no privacy notice to point at. Memory persistence stores nothing on the
       * visitor's device, so there is nothing to consent to.
       *
       * What it costs: the distinct id lives for the lifetime of the JavaScript
       * context, so client-side navigation within a visit stays one id and a
       * full reload starts a new one. Returning visitors cannot be recognised
       * and retention is not measurable. That is an acceptable trade for a docs
       * site whose actual question is "does anyone reach section 03", which is a
       * count.
       *
       * `identified_only` keeps it from creating a person profile per anonymous
       * visitor, which would be a stored identity in all but name.
       */
      persistence: 'memory',
      person_profiles: 'identified_only',
    });
  }
}
