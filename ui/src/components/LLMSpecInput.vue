<template>
  <section class="bg-dark-card rounded-lg p-6 shadow-lg">
    <div @click="toggleLLMSpec" class="flex justify-between items-center cursor-pointer">
      <h2 class="text-2xl font-bold">LLM API Spec</h2>
      </div>

    <div v-show="showLLMSpec" class="mt-4">
      <label v-if="isFocused" for="llm-spec" class="block text-sm font-medium mb-2">
        LLM API Spec, PROMPT variable will be replaced with the testing prompt
      </label>
      </div>
  </section>
</template>

<script>
export default {
  name: 'LLMSpecInput',
  data() {
    return {
      showLLMSpec: false,
      isFocused: false,
       modelSpec: '',
      errorMsg: null,
      okMsg: null,
    };
  },
  methods: {
       toggleLLMSpec() {
      this.showLLMSpec = !this.showLLMSpec;
    },
    focusTextarea() {
      this.isFocused = true;
    },
    unfocusTextarea() {
      this.isFocused = false;
    },
    adjustHeight(event) {
      event.target.style.height = 'auto';
      event.target.style.height = event.target.scrollHeight + 'px';
    },
    verifyIntegration() {
      // Your logic for verifying integration
    },
  },
  computed: {
    highlightedText() {
      // Your logic for highlighted text
    },
     statusDotClass() {
      // Your logic for status dot class
    },
  },
};
</script>

<style scoped>
/* Styles for the LLM Spec Input */
</style>
