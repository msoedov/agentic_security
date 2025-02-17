<template>
  <div>hello</div>
</template>

<script>
export default {
  name: 'PageHeader', // Give a descriptive name
  // No specific JavaScript logic needed for this simple header
  // You can add props if you want to make the title dynamic:
  props: {
    title: {
      type: String,
      default: 'LLM Vulnerability Scanner' // Default title
    }
  }
};
</script>

<style scoped>
/* Any header-specific styles can go here */
/* If you are using tailwind, you can include this as well*/
</style>
