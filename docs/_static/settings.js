'use-strict';

let settingsModal;

class Setting {
  constructor(name, defaultValue, setter) {
    this.name = name;
    this.defaultValue = defaultValue;
    this.setValue = setter;
  }

  setElement() {
    throw new TypeError('Abstract methods should be implemented.');
  }

  load() {
    let value = JSON.parse(localStorage.getItem(this.name));
    this.value = value === null ? this.defaultValue : value;
    try {
      this.setValue(this.value);
    } catch (error) {
      console.error(`Failed to apply setting "${this.name}" With value:`, this.value);
      console.error(error);
    }
  }

  update() {
    throw new TypeError('Abstract methods should be implemented.');
  }

}

class CheckboxSetting extends Setting {

  setElement() {
    let element = document.querySelector(`input[name=${this.name}]`);
    element.checked = this.value;
  }

  update(element) {
    localStorage.setItem(this.name, element.checked);
    this.setValue(element.checked);
  }

}

class RadioSetting extends Setting {

  setElement() {
    let element = document.querySelector(`input[name=${this.name}][value=${this.value}]`);
    element.checked = true;
  }

  update(element) {
    localStorage.setItem(this.name, `"${element.value}"`);
    this.setValue(element.value);
  }

}

/**
* Toggles the `data-test` attribute on and off.
* @param {boolean} set -
Whether to set or remove the attribute.
 */
function getRootAttributeToggle(attributeName, valueName) {
  /**
  * Sets or removes a data attribute on the document element.
  * @param
  {string} attributeName The name of the data attribute to set or remove.
  *
  @param {boolean} set Whether to set or remove the data attribute.
   */
  function toggleRootAttribute(set) {
    if (set) {
      document.documentElement.setAttribute(`data-${attributeName}`, valueName);
    } else {
      document.documentElement.removeAttribute(`data-${attributeName}`);
    }
  }
  return toggleRootAttribute;
}

/**
* Sets the document's data-theme attribute to either 'light' or 'dark',
depending on the value of `value`.
* @param {string} value The value to
set. Must be one of: "light", "dark", or "automatic".
 */
function setTheme(value) {
  if (value === 'automatic') {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  }
  else {
    document.documentElement.setAttribute('data-theme', value);
  }
}

const settings = [
  new CheckboxSetting('useSerifFont', false, getRootAttributeToggle('font', 'serif')),
  new RadioSetting('setTheme', 'automatic', setTheme)
]

function updateSetting(element) {
  let setting = settings.find((s) => s.name == element.name);
  if (setting) {
    setting.update(element);
  }
}

for (const setting of settings) {
  setting.load();
}

document.addEventListener('DOMContentLoaded', () => {
  settingsModal = new Modal(document.querySelector('div#settings.modal'));
  for (const setting of settings) {
    setting.setElement();
  }
});
