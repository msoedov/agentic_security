<template>
  <footer class="mt-16 pt-8 border-t border-gray-800">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <h3 class="text-lg font-semibold text-dark-accent-green mb-4">Home</h3>
          <p class="text-gray-400">Dedicated to LLM Security, 2024</p>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-dark-accent-green mb-4">Connect</h3>
          <ul class="space-y-2">
            <li>
              <a
                href="https://x.com"
                target="_blank"
                rel="noopener noreferrer"
                class="text-gray-400 hover:text-dark-accent-green"
                >X.com</a
              >
            </li>
            <li>
              <a
                href="https://github.com/msoedov"
                target="_blank"
                rel="noopener noreferrer"
                class="text-gray-400 hover:text-dark-accent-green"
                >Github</a
              >
            </li>
          </ul>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-dark-accent-green mb-4">About</h3>
          <p class="text-gray-400">
            This is the LLM Vulnerability Scanner. Easy to use—no coding
            needed, just pure security testing.
          </p>
        </div>
      </div>

      <div class="mt-8 pt-8 border-t border-gray-800 text-center">
        <p class="text-gray-400">Made with ❤️ by the Agentic Security Team</p>
      </div>
    </div>
  </footer>
</template>

<script>
export default {
  name: 'PageFooter', // Descriptive name
};
</script>

<style scoped>
/* Footer-specific styles here */
</style>