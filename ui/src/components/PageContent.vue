<template>
   <div id="consent-modal" v-if="showConsentModal"
    class="fixed inset-0 bg-black bg-opacity-75 flex justify-center items-center z-50">
    <div
        class="bg-dark-card text-dark-text p-8 rounded-xl shadow-2xl max-w-xl w-full">
        <h2 class="text-2xl font-bold mb-6 text-center">AI Red Team Ethical
            Use Agreement</h2>
        <div class="space-y-6">
            <p class="text-sm leading-relaxed">
                This AI red team tool is designed for security research,
                vulnerability assessment,
                and responsible testing purposes. By accessing this tool, you
                explicitly agree to
                the following ethical guidelines:
            </p>
            <ul class="list-disc list-inside text-sm space-y-3">
                <li>
                    <strong>Consent and Authorization:</strong> You will only
                    use
                    this tool on systems
                    for which you have explicit, documented permission from the
                    system owners.
                </li>
                <li>
                    <strong>Responsible Disclosure:</strong> Any vulnerabilities
                    discovered must be
                    reported responsibly to the appropriate parties,
                    prioritizing
                    system and user safety.
                </li>
                <li>
                    <strong>No Malicious Intent:</strong> You will not use this
                    tool
                    to cause harm,
                    disrupt services, or compromise the integrity of any system
                    or
                    data.
                </li>
                <li>
                    <strong>Legal Compliance:</strong> All testing and research
                    must
                    comply with
                    applicable local, national, and international laws and
                    regulations.
                </li>

            </ul>

            <p class="text-xs text-gray-400 italic">
                Violation of these terms may result in immediate termination of
                access and
                potential legal consequences.
            </p>
        </div>
        <div class="flex justify-center space-x-4 mt-8">
            <button
                @click="declineConsent"
                class="bg-dark-accent-red text-white rounded-lg px-6 py-3 font-medium hover:bg-opacity-80 transition-colors">
                Decline
            </button>
            <button
                @click="acceptConsent"
                class="bg-dark-accent-green text-dark-bg rounded-lg px-6 py-3 font-medium hover:bg-opacity-80 transition-colors">
                I Agree and Understand
            </button>
        </div>
    </div>
    
</div>


</template>

<script>
export default {
  name: 'PageContent',

  data() {
    return {
      showConsentModal: true // Default to true
    };
  },

  emits: ['accept', 'decline'], // Define the custom events

  methods: {
     acceptConsent() {
            this.showConsentModal = false; // Close the modal
            localStorage.setItem('consentGiven', 'true'); // Save consent to local storage
        },
    declineConsent() {
            this.showConsentModal = false; // Close the modal
            localStorage.setItem('consentGiven', 'false'); // Save decline to local storage
            window.location.href = 'https://www.google.com'; // Redirect to Google
        },
  }
};
</script>


<style >
/* Styles for the consent modal */
</style>