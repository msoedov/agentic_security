module.exports = {
    env: {
      browser: true,
      es2021: true,
      node :true
    },
    extends: [
      'eslint:recommended',
      'plugin:vue/essential',
    ],
    parserOptions: {
      ecmaVersion: 12,
      sourceType: 'module',
    },
    plugins: [
      'vue',
    ],
    rules: {
      'no-unused-vars': 'off', // Disable the rule
      'no-constant-condition': 'off',
      'no-global-assign': 'off',
      // or
      // 'no-unused-vars': 'warn', // Change the rule to a warning
    },
  };