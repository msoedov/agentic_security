<template>
     <main class="max-w-6xl mx-auto space-y-8">
        <section class="bg-dark-card rounded-lg p-6 shadow-lg">
          <h2 class="text-2xl font-bold mb-4">Select a Config</h2>

          <div class="flex space-x-4 overflow-x-auto scrollbar-hide">
            <div
              v-for="(config, index) in configs"
              :key="index"
              @click="selectConfig(index)"
              class="flex-none w-1/2 sm:w-1/3 md:w-1/4 lg:w-1/5 border-2 rounded-lg p-4 flex flex-col items-start transition-all hover:shadow-md cursor-pointer"
              :class="{
        'border-dark-accent-green': selectedConfig === index,
        'border-gray-600': selectedConfig !== index
      }">
              <div class="font-medium mb-2">{{ config.name }}</div>
              <div class="text-sm text-gray-400">
                {{ config.customInstructions || 'Requires API key' }}
              </div>
              <div class="mt-2 text-dark-accent-green font-semibold">
                {{config.modality || 'API'}}</div>
            </div>
          </div>
        </section>

        <!-- Collapsible LLM Spec Input -->
        <section class="bg-dark-card rounded-lg p-6 shadow-lg" >
          <div @click="toggleLLMSpec"
            class="flex justify-between items-center cursor-pointer">

            <h2 class="text-2xl font-bold">LLM API Spec</h2>
            <span :class="statusDotClass"
              class="w-3 h-3 rounded-full mr-2"></span>
            <svg :class="{'rotate-180': showLLMSpec}"
              class="w-6 h-6 transition-transform duration-200"
              xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>

          <div v-show="showLLMSpec" class="mt-4">
            <label v-if="isFocused" for="llm-spec"
              class="block text-sm font-medium mb-2">
              LLM API Spec, PROMPT variable will be replaced with the testing
              prompt
            </label>
            <div
              v-if="!isFocused"
              
              class="w-full bg-dark-bg text-dark-accent-orange border border-gray-600 rounded-lg p-3 cursor-text mb-5"
              @click="focusTextarea"
              v-html="highlightedText"></div>

            <textarea
              v-else
              ref="textarea"
              class="w-full bg-dark-bg text-dark-accent-orange border border-gray-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-dark-accent-green"
              @blur="unfocusTextarea"
              v-model="modelSpec"
              @input="adjustHeight"
              rows="5"
              placeholder="Enter LLM API Spec here..."></textarea>

            <!-- Error and Success Messages -->
            <div v-if="errorMsg"
              class="bg-dark-accent-red bg-opacity-20 border border-dark-accent-red text-dark-accent-red px-4 py-3 rounded-lg relative"
              role="alert">
              <strong class="font-bold">Oops!</strong>
              <span class="block sm:inline">{{errorMsg}}</span>
            </div>
            <div v-if="okMsg"
              class="bg-dark-accent-green bg-opacity-20 border border-dark-accent-green text-dark-accent-green px-4 py-3 rounded-lg relative"
              role="alert">
              <strong class="font-bold"></strong>
              <span class="block sm:inline">{{okMsg}}</span>
            </div>

            <!-- Action Buttons -->
            <section class="flex justify-center space-x-4 mt-10">
              <button
                @click="verifyIntegration"
                class="bg-dark-accent-orange text-dark-bg rounded-lg px-6 py-3 font-medium hover:bg-opacity-80 transition-colors">
                Verify Integration
              </button>
            </section>
          </div>
        </section>
        <!-- LLM Spec Input -->
     <section class="bg-dark-card rounded-lg p-6 shadow-lg" v-if="false" >
          <h2 class="text-2xl font-bold mb-4">LLM API Spec</h2>
          <label for="llm-spec" class="block text-sm font-medium mb-2">
            LLM API Spec, PROMPT variable will be replaced with the testing
            prompt
          </label>
          <textarea
            class="w-full bg-dark-bg text-dark-accent-orange border border-gray-600 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-dark-accent-green"
            id="llm-spec"
            ref="textarea"
            v-model="modelSpec"
            @input="adjustHeight"
            rows="5"
            placeholder="Enter LLM API Spec here..."></textarea>
        </section>
        <section
          class="bg-dark-card rounded-lg p-6 shadow-lg mt-8 border-dark-accent-green border-2">
          <div @click="toggleParams"
            class="flex justify-between items-center cursor-pointer">
            <div class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2"
                fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              <h2 class="text-2xl font-bold">Parameters</h2>
            </div>
            <svg :class="{'rotate-180': showParams}"
              class="w-6 h-6 transition-transform duration-200"
              xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
          <div v-show="showParams" class="mt-4">
            <div class="flex items-center justify-end mt-4">
              <button
                @click="confirmResetState"
                class="flex items-center bg-dark-accent-red text-dark-bg rounded-lg px-4 py-2 text-sm font-medium hover:bg-opacity-80 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reset State
              </button>
            </div>
            <!-- Confirmation Modal -->
            <div
              v-if="showResetConfirmation"
              class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div class="bg-dark-card rounded-lg p-6 max-w-sm w-full">
                <h3 class="text-xl font-bold mb-4 text-dark-text">Confirm
                  Reset</h3>
                <p class="text-gray-400 mb-6">Are you sure you want to reset all
                  settings to their default state? This action cannot be
                  undone.</p>
                <div class="flex justify-end space-x-4">
                  <button
                    @click="showResetConfirmation = false"
                    class="bg-gray-600 text-dark-text rounded-lg px-4 py-2 hover:bg-opacity-80 transition-colors">
                    Cancel
                  </button>
                  <button
                    @click="resetState"
                    class="bg-dark-accent-red text-dark-bg rounded-lg px-4 py-2 hover:bg-opacity-80 transition-colors">
                    Reset
                  </button>
                </div>
              </div>
            </div>
            <!-- Confirmation Modal -->

            <!-- Maximum Budget Slider -->
            <!-- Budget Slider -->
            <section class="bg-dark-card rounded-lg p-6 shadow-lg">
              <h2 class="text-2xl font-bold mb-4">Maximum Budget</h2>
              <div class="flex justify-between items-center mb-4">
                <span class="text-lg">1M Tokens</span>
                <input
                  v-model="budget"
                  @change="updateBudgetFromInput"
                  class="w-20 bg-dark-bg text-dark-text border border-gray-600 rounded-lg p-2 text-center"
                  type="text" />
                <span class="text-lg">100M Tokens</span>
              </div>
              <input
                v-model="budget"
                @input="updateBudgetFromSlider"
                type="range"
                min="1"
                max="100"
                step="1"
                class="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer">
            </section>

            <!-- Optimize Toggle -->
            <div class="flex flex-col mt-6 mr-10 ml-10">
              <div class="flex items-center justify-between mb-2">
                <h3 class="text-lg font-semibold">Optimize Test</h3>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="optimize"
                    class="sr-only peer">
                  <div
                    class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dark-accent-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-dark-accent-green"></div>
                </label>
              </div>
              <p class="text-sm text-gray-400 mt-2 mb-6">
                When enabled, this option runs a Bayesian optimization loop to
                find the most effective test parameters. This can potentially
                reduce the cost and the total running time of your vulnerability
                scan, but may reduce accuracy.
              </p>

              <!-- Chart Diagram Toggle -->
              <div class="flex items-center justify-between mb-2">
                <h3 class="text-lg font-semibold">Enable Chart Diagram</h3>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="enableChartDiagram"
                    class="sr-only peer">
                  <div
                    class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dark-accent-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-dark-accent-green"></div>
                </label>
              </div>
              <p class="text-sm text-gray-400 mt-2 mb-6">
                When enabled, a chart diagram will be generated to visualize the
                results of your vulnerability scan.
              </p>

              <!-- Logging Toggle -->
              <div class="flex items-center justify-between mb-2">
                <h3 class="text-lg font-semibold">Enable Detailed Logging</h3>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="enableLogging"
                    class="sr-only peer">
                  <div
                    class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dark-accent-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-dark-accent-green"></div>
                </label>
              </div>
              <p class="text-sm text-gray-400 mt-2 mb-6">
                When enabled, detailed logs will be generated during the
                vulnerability scan process. This can be useful for debugging and
                in-depth analysis.
              </p>

              <!-- Concurrency Toggle -->
              <div class="flex items-center justify-between mb-2">
                <h3 class="text-lg font-semibold">Enable Concurrency</h3>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" v-model="enableConcurrency"
                    class="sr-only peer">
                  <div
                    class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dark-accent-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-dark-accent-green"></div>
                </label>
              </div>
              <p class="text-sm text-gray-400 mt-2">
                When enabled, the vulnerability scan will run multiple tests
                concurrently. This can significantly reduce the total scan time
                but may increase resource usage.
              </p>
            </div>
          </div>
        </section>

        <!-- Modules Selection -->
        <section
          class="bg-dark-card rounded-lg p-6 shadow-lg border-dark-accent-red border-4">
          <div @click="toggleModules"
            class="flex justify-between items-center cursor-pointer">
            <h2 class="text-2xl font-bold">Modules [{{selectedDS}}
              selected]</h2>
            <svg :class="{'rotate-180': showModules}"
              class="w-6 h-6 transition-transform duration-200"
              xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>

          <div v-show="showModules" class="mt-4">
            <!-- Many-shot jailbreaking Toggle -->
            <div v-if="enableMultiStepAttack" class="alert-box mt-4">
              <div
                class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative"
                role="alert">
                <strong class="font-bold">Notice:</strong>
                <span class="block sm:inline">A many-shot attack might take a
                  longer time to complete.
                </span>
              </div>
            </div>
            <div class="flex items-center justify-between mb-2 mt-10">
              <h3 class="text-lg font-semibold">Enable Many-shot
                jailbreaking</h3>

              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="enableMultiStepAttack"
                  class="sr-only peer">
                <div
                  class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dark-accent-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-dark-accent-green"></div>
              </label>
            </div>
            <p class="text-sm text-gray-400 mt-2 mb-2">
              When enabled, the scan will attempt Many-shot jailbreaking
              simulations
            </p>

            <div v-if="hasFileSpec" class="alert-box mt-10">
              <div
                class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative"
                role="alert">
                <strong class="font-bold">Notice:</strong>
                <span class="block sm:inline">Converting audio or image prompts
                  might
                  take some time to compute.</span>
              </div>
            </div>

            <div class="flex justify-between mb-4 mt-4">
              <button @click="selectAllPackages"
                class="text-dark-accent-green hover:underline">Select
                All</button>
              <button @click="deselectAllPackages"
                class="text-gray-400 hover:underline">Deselect All</button>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              <div
                v-for="(pkg, index) in dataConfig"
                :key="index"
                @click="addPackage(index)"
                class="border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md overflow-hidden"
                :class="{
                'border-dark-accent-green bg-dark-accent-green bg-opacity-20': pkg.selected,
                'border-gray-600': !pkg.selected
              }">
                <div class="font-medium mb-1 truncate">{{ pkg.dataset_name
                  }}</div>
                <div class="text-sm text-gray-400 truncate">
                  {{ pkg.source || 'Local dataset' }}
                </div>
                <div class="mt-2 text-sm font-semibold">
                  {{ pkg.dynamic ? 'Dynamic dataset' :
                  `${pkg.num_prompts.toLocaleString()} prompts` }}
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Error and Success Messages -->
        <div v-if="errorMsg"
          class="bg-dark-accent-red bg-opacity-20 border border-dark-accent-red text-dark-accent-red px-4 py-3 rounded-lg relative"
          role="alert">
          <strong class="font-bold">Oops!</strong>
          <span class="block sm:inline">{{errorMsg}}</span>
        </div>
        <div v-if="okMsg"
          class="bg-dark-accent-green bg-opacity-20 border border-dark-accent-green text-dark-accent-green px-4 py-3 rounded-lg relative"
          role="alert">
          <strong class="font-bold">></strong>
          <span class="block sm:inline">{{okMsg}}</span>
        </div>

        <!-- Action Buttons -->
        <section class="flex justify-center space-x-4">
          <button
            @click="verifyIntegration"
            class="bg-dark-accent-orange text-dark-bg rounded-lg px-6 py-3 font-medium hover:bg-opacity-80 transition-colors">
            Verify Integration
          </button>
          <button
            @click="startScan"
            v-if="!scanRunning"
            class="bg-dark-accent-green text-dark-bg rounded-lg px-6 py-3 font-medium hover:bg-opacity-80 transition-colors flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
              viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              class="mr-2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            Run Scan
          </button>
          <button
            @click="stopScan"
            v-if="scanRunning"
            class="bg-dark-accent-red text-dark-bg rounded-lg px-6 py-3 font-medium hover:bg-opacity-80 transition-colors flex items-center">
            <!-- Stop Icon -->
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
              viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              class="mr-2"><rect x="6" y="6" width="12"
                height="12"></rect></svg>
            Stop Scan
          </button>
        </section>

        <!-- Progress Bar -->
        <div id="progress"
          class="bg-dark-accent-green rounded-full h-2 transition-all duration-500 ease-in-out"
          v-bind:style="{width: progressWidth}">
        </div>

        <!-- Scan Results -->
        <section class="bg-dark-card rounded-lg p-6 shadow-lg"
          v-if="mainTable.length > 0">
          <h2 class="text-2xl font-bold mb-4">Scan Results</h2>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-gray-600">
                  <th class="p-3">Vulnerability Module</th>
                  <th class="p-3">% Strength</th>
                  <th class="p-3">Number of Tokens</th>
                  <th class="p-3">Cost (in gpt-3 tokens)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="result in mainTable" :key="result.module || index" class="border-b border-gray-700"
                  :class="{'text-dark-accent-green': result.last, 'text-gray-300': !result.last}">
                  <td class="p-3">{{result.module}}</td>
                  <td class="p-3 text-gray-100"
                    :class="getFailureRateColor(result.failureRate)">
                    {{getFailureRateScore(result.failureRate)}}( {{(100 -
                    result.failureRate).toFixed(2)}} )
                  </td>
                  <td class="p-3">{{result.tokens}}k</td>
                  <td class="p-3">${{result.cost.toFixed(2)}}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Download Button -->
        <button
          @click="downloadFailures"
          class="bg-dark-accent-yellow text-dark-bg rounded-lg px-6 py-3 font-medium hover:bg-opacity-80 transition-colors">
          Download failures
        </button>

        <!-- Report Image -->
        <img :src="reportImageUrl" alt="Generated Plot" v-if="reportImageUrl"
          loading="lazy" class="mx-auto rounded-lg shadow-lg">

        <!-- Logs Section -->
        <section class="bg-dark-card rounded-lg p-6 shadow-lg mt-8">
          <div @click="toggleLogs"
            class="flex justify-between items-center cursor-pointer">
            <h2 class="text-2xl font-bold">Logs</h2>
            <svg :class="{'rotate-180': showLogs}"
              class="w-6 h-6 transition-transform duration-200"
              xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>

          <div v-show="showLogs" class="mt-4">
            <div class="mb-4 flex justify-between items-center">
              <span class="text-sm text-gray-400">Showing latest {{
                Math.min(logs.length, maxDisplayedLogs) }} of {{ logs.length }}
                logs</span>
              <button @click="downloadLogs"
                class="bg-dark-accent-green text-dark-bg rounded-lg px-4 py-2 text-sm font-medium hover:bg-opacity-80 transition-colors">
                Download Logs
              </button>
            </div>
            <div class="bg-dark-bg p-4 rounded-lg max-h-96 overflow-y-auto">
              <div v-for="(log, index) in displayedLogs" :key="index"
                class="mb-2 last:mb-0">
                <span class="text-dark-accent-green">{{ log.timestamp }}</span>
                <span class="ml-2"
                  :class="{'text-dark-accent-red': log.level === 'ERROR'}">{{
                  log.message }}</span>
              </div>
            </div>
          </div>
        </section>
      </main>
</template>
<script>
import { LLM_CONFIGS, LLM_SPECS,has_image, has_files, _getFailureRateColor, _getFailureRateScore,URL } from '../../public/base.js';
import { ref, useTemplateRef, onMounted } from 'vue'

const textarea= useTemplateRef('textarea')
export default{
    name: 'PageConfigs',
    data(){
        return {
        progressWidth: '0%',
        modelSpec: LLM_SPECS[0],
        budget: 50,
        isFocused: false, // Tracks if the textarea is focused
        showParams: false,
        showResetConfirmation: false,
        enableChartDiagram: true,
        enableLogging: false,
        enableConcurrency: false,
        optimize: false,
        enableMultiStepAttack: false,
        scanResults: [],
        mainTable: [],
        integrationVerified: false,
        scanRunning: false,
        errorMsg: '',
        maskMode: false,
        okMsg: '',
        reportImageUrl: '',
        selectedConfig: 0,
        showModules: false,
        showLogs: false,
        showConsentModal: true,
        statusDotClass: 'bg-gray-500', // Default status dot class
        statusText: 'Verified', // Default status text
        statusClass: 'bg-green-500 text-dark-bg', // Default status class
        showLLMSpec: true, // Default to showing the LLM Spec Input
        logs: [], // This will store all the logs
        maxDisplayedLogs: 50, // Maximum number of logs to display
        configs: LLM_CONFIGS,
        dataConfig: [],
    }
    },   
    created() {
        // Check if consent is already given in local storage
        const consentGiven = localStorage.getItem('consentGiven');
        if (consentGiven === 'true') {
            this.showConsentModal = false; // Don't show the modal if consent was given
        }
    },
    mounted: function () {
        this.adjustHeight({ target: this.$refs.textarea }); 
        // this.startScan();
        this.loadConfigs();

    },
    computed: {
        selectedDS: function () {
            return this.dataConfig.filter(p => p.selected).length;
        },
        displayedLogs() {
            return this.logs.slice(-this.maxDisplayedLogs).reverse();
        },
        hasImageSpec() {
            return has_image(this.modelSpec);
        },
        hasAudioSpec() {
            return has_files(this.modelSpec);
        },
        hasFileSpec() {
            return has_files(this.modelSpec) || has_image(this.modelSpec);
        },
        highlightedText() {
            // First highlight <<VAR>> pattern
            let text = this.modelSpec.replace(
                /<<([^>]+)>>/g,
                `<span class="px-2 py-0.5 rounded-full bg-dark-accent-yellow text-dark-bg font-medium">&lt;&lt;$1&gt;&gt;</span>`
            );

            // Then highlight $VARIABLE pattern
            text = text.replace(
                /(\$[A-Z_]+)/g,
                `<span class="px-2 py-0.5 rounded-full bg-yellow-100 text-dark-bg font-medium">$1</span>`
            );

            // Finally wrap everything in gray text
            return `<span class="text-gray-500">${text}</span>`;
        },
        highlightedText2() {
            // First apply the highlighting for variables
            const highlightedText = this.modelSpec.replace(
                /<<([^>]+)>>/g,
                `<span class="px-2 py-0.5 rounded-full bg-dark-accent-yellow text-dark-bg font-medium">&lt;&lt;$1&gt;&gt;</span>`
            );

            // Wrap the entire text in a span to make non-highlighted parts dim gray
            return `<span class="text-gray-500">${highlightedText}</span>`;
        }

    },
    methods: {
        focusTextarea() {
            this.isFocused = true;
            self = this.$refs;
            this.$nextTick(() => {
                // Focus the textarea after rendering
                this.$refs.textarea?.focus();
                this.adjustHeight({ target: this.$refs.textarea });
            });
            document.addEventListener("mousedown", this.handleClickOutside);

        },
        handleOutsideClick(event) {
            if (!this.$refs.container.contains(event.target)) {
                this.isFocused = false;
                document.removeEventListener("mousedown", this.handleClickOutside);
            }
        },
        unfocusTextarea() {
            this.isFocused = false;
        },
        acceptConsent() {
            this.showConsentModal = false; // Close the modal
            localStorage.setItem('consentGiven', 'true'); // Save consent to local storage
        },

        saveStateToLocalStorage() {
            const state = {
                modelSpec: this.modelSpec,
                budget: this.budget,
                dataConfig: this.dataConfig,
                optimize: this.optimize,
                enableChartDiagram: this.enableChartDiagram,
                enableMultiStepAttack: this.enableMultiStepAttack,
            };
            localStorage.setItem('appState:v1', JSON.stringify(state));
        },
        loadStateFromLocalStorage() {
            const savedState = localStorage.getItem('appState:v1');
            console.log('Loading state from local storage:', savedState);
            if (savedState) {
                const state = JSON.parse(savedState);
                this.modelSpec = state.modelSpec;
                this.budget = state.budget;
                this.dataConfig = state.dataConfig;
                this.optimize = state.optimize;
                this.enableChartDiagram = state.enableChartDiagram;
                this.enableMultiStepAttack = state.enableMultiStepAttack;
            }
        },
        resetState() {
            localStorage.removeItem('appState:v1');
            this.modelSpec = LLM_SPECS[0];
            this.budget = 50;
            this.dataConfig.forEach(config => config.selected = false);
            this.optimize = false;
            this.enableChartDiagram = true;
            this.okMsg = '';
            this.errorMsg = '';
            this.integrationVerified = false;
            this.showResetConfirmation = false;
            this.enableMultiStepAttack = false;
        },
        confirmResetState() {
            this.showResetConfirmation = true;
        },
        updateStatusDot(ok) {
            if (ok) {
                this.statusDotClass = 'bg-green-500'; // Green when expanded
            } else if (!ok) {
                this.statusDotClass = 'bg-orange-500'; // Orange if collapsed with content
            } else {
                this.statusDotClass = 'bg-gray-500'; // Gray if collapsed without content
            }
        },
        toggleLLMSpec() {
            this.showLLMSpec = !this.showLLMSpec;
        },
        // adjustHeight(event) {
        //   console.log(event,"event")
        //     const textarea = event.target;
        //     event.target.style.height = 'auto';
        //     event.target.style.height = event.target.scrollHeight + 'px';
        // },
        downloadFailures() {
            window.open('/failures', '_blank');
        },
        hide() {
            this.maskMode = !this.maskMode;
        },
        verifyIntegration: async function () {
            let payload = {
                spec: this.modelSpec,
            };
            const response = await fetch(`${URL}/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
            console.log(response);
            let txt = await response.text();
            if (!response.ok) {
                this.updateStatusDot(false);
                this.errorMsg = 'Integration verification failed:' + txt;
            } else {
                this.errorMsg = '';
                this.updateStatusDot(true);
                this.okMsg = 'Integration verified';
                this.integrationVerified = true;
                // console.log('Integration verified', this.integrationVerified);
                // this.$forceUpdate();

            }
            this.saveStateToLocalStorage();
        },
        loadConfigs: async function () {
            const response = await fetch(`${URL}/v1/data-config`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            console.log(response);
            this.dataConfig = await response?.json();
            this.loadStateFromLocalStorage();
        },
        selectConfig(index) {
            this.selectedConfig = index;
            this.modelSpec = LLM_SPECS[index];
            this.adjustHeight({ target: this.$refs.textarea });
            // this.adjustHeight({ target: document.getElementById('llm-spec') });
            this.errorMsg = '';
            this.okMsg = '';
            this.integrationVerified = false;
        },
        toggleModules() {
            this.showModules = !this.showModules;
        },
        toggleLogs() {
            this.showLogs = !this.showLogs;
        },
        addLog(message, level = 'INFO') {
            const timestamp = new Date().toISOString();
            this.logs.push({ timestamp, message, level });
        },
        downloadLogs() {
            const logText = this.logs.map(log => `${log.timestamp} [${log.level}] ${log.message}`).join('\n');
            const blob = new Blob([logText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'vulnerability_scan_logs.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        },
        addPackage(index) {

             const pkg = this.dataConfig[index];
            pkg.selected = !pkg.selected;

        },
        getFailureRateScore(failureRate) {
            return _getFailureRateScore(failureRate);
        },
        getFailureRateColor(failureRate) {
            return _getFailureRateColor(failureRate);
        },
        toggleParams() {
            this.showParams = !this.showParams;
        },
        adjustHeight(event) {
            const element = event.target;
            if (!element) {
                return
            }
            // Reset height to ensure accurate measurement
            element.style.height = 'auto';
            // Adjust height based on scrollHeight
            element.style.height = `${element.scrollHeight + 100}px`;
        },
        newEvent: function (event) {

            if (event.status) {
                this.okMsg = `${event.module}`;
                return
            }
            console.log('New event');
            //  { "module": "Module 49", "tokens": 480, "cost": 4.800000000000001, "progress": 9.8 }
            let progress = event.progress;
            progress = progress % 100;
            this.progressWidth = `${progress}%`;
            this.addLog(`${JSON.stringify(event)}`, 'INFO');
            if (this.mainTable.length < 1) {
                this.mainTable.push(event);
                event.last = true;

                return
            }
            let last = this.mainTable[this.mainTable.length - 1];
            if (last.module === event.module) {
                last.tokens = event.tokens;
                last.cost = event.cost;
                last.progress = event.progress;
                last.failureRate = event.failureRate;
            } else {
                last.last = false;
                this.mainTable.push(event);
                event.last = true;
                this.newRow()
            }
            this.okMsg = `New event: ${event.module}: ${event.progress}%`;

        },
        newRow: async function () {
            if (!this.enableChartDiagram) {
                return
            }
            console.log('New row');
            let payload = {
                table: this.mainTable,
            };
            const response = await fetch(`${URL}/plot.jpeg`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
            // Convert image response to a data URL for the <img> src
            const blob = await response.blob();
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = () => {
                this.reportImageUrl = reader.result;
            };
        },
        selectAllPackages() {
            const allSelected = this.dataConfig.every(pkg => pkg.selected);

            // If all are selected, deselect all. Otherwise, select all.
            this.dataConfig.forEach(pkg => {
                pkg.selected = !allSelected;
            });

            this.updateSelectedDS();
        },

        deselectAllPackages() {
            this.dataConfig.forEach(pkg => {
                pkg.selected = false;
            });
            this.updateSelectedDS();
        },

        updateSelectedDS() {
            this.selectedDS = this.dataConfig.filter(pkg => pkg.selected).length;
        },
        updateBudgetFromSlider(event) {
            this.budget = parseInt(event.target.value);
        },
        updateBudgetFromInput(event) {
            let value = parseInt(event.target.value);
            if (isNaN(value) || value < 1) {
                value = 1;
            } else if (value > 100) {
                value = 100;
            }
            this.budget = value;
        },
        stopScan: async function () {
            this.scanRunning = false;
            const response = await fetch(`${URL}/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
        },
        startScan: async function () {
            this.showLLMSpec = false;
            let payload = {
                maxBudget: this.budget,
                llmSpec: this.modelSpec,
                datasets: this.dataConfig,
                optimize: this.optimize,
                enableMultiStepAttack: this.enableMultiStepAttack,
            };
            const response = await fetch(`${URL}/scan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
            this.okMsg = 'Scan started';
            this.mainTable = [];
            this.scanRunning = true;
            const reader = response.body.getReader();
            let receivedLength = 0; // received that many bytes at the moment
            let chunks = []; // array of received binary chunks (comprises the body)
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                chunks.push(value);
                receivedLength += value.length;

                const chunkAsString = new TextDecoder("utf-8").decode(value);
                const chunkAsLines = chunkAsString.split('\n').filter(line => line.trim());

                self = this;
                chunkAsLines.forEach(line => {
                    try {
                        const result = JSON.parse(line);
                        self.scanResults.push(result);
                        self.newEvent(result);
                    } catch (e) {
                        console.error('Error parsing chunk:', e);
                    }
                });
            }
            this.saveStateToLocalStorage();

        }
    }
}
</script>
