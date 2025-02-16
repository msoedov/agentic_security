<template>
  <div>
         <div
        class="bg-dark-accent-green text-dark-bg py-4 px-6 rounded-lg mb-28 text-center">
        <h4 class="text-lg font-semibold">
          🚀 NEW: Star Agentic Security on
          <a href="https://github.com/msoedov/agentic_security" target="_blank"
            class="underline" data-faitracker-click-bind="true">Github</a> 🚀
        </h4>
      </div>

      <!-- Header with Github link -->
      <header class="flex justify-between items-center mb-8 relative"
        v-if="false">
        <div class="w-full absolute left-0 flex justify-center">
          <h1
            class="text-2xl font-bold text-gray-400"> <span
              class="text-2xl font-technopollas  text-gray-300">Agentic
            </span>

            Vulnerability
            Scanner</h1>
        </div>
</header>
<PageContent/>
<PageConfigs/>
    <PageFooter />
    </div>
  
</template>

<script>
import PageFooter from "./components/PageFooter.vue";
import PageContent from "./components/PageContent.vue";
import PageConfigs from "./components/PageConfigs.vue";





export default {
  components: {
    PageFooter,
    PageContent,
    PageConfigs
  }
};
</script>

<style scoped>
/* Global styles or App.vue specific styles */
</style>
