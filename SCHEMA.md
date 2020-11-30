# Forms Schema

Since MongoDB has no set schema, we document it here to document what our objects should look like. If you add new properties or remove them from objects **make sure to update them here**.

In this document:
- [Form structure](#Form_structure)
    - [Form features](#Form_features)
    - [Form question](#Form_question)

## Form structure

| Field       | Type                                     | Description                                                                               | Example                     |
| ----------- | ---------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------- |
| `id`        | Unique identifier                        | A user selected, unique, descriptive identifier (used in URL routes, so no spaces)        | `"ban-appeals"`             |
| `features`  | List of [form features](#Form_features)  | A list of features to change the behaviour of the form, described in the features section | `["OPEN", "COLLECT_EMAIL"]` |
| `questions` | List of [form questions](#Form_question) | The list of questions to render on a specific form                                        | Too long! See below         |
|             |                                          |                                                                                           |                             |

### Form features

| Flag               | Description                                                                   |
| ------------------ | ----------------------------------------------------------------------------- |
| `DISCOVERABLE`     | The form should be displayed on the homepage of the forms application.        |
| `REQUIRES_LOGIN`   | Requires the user to authenticate with Discord before completing the form.    |
| `OPEN`             | The form is currently accepting responses.                                    |
| `COLLECT_EMAIL`    | The form should collect the email from submissions. Requires `REQUIRES_LOGIN` |
| `DISABLE_ANTISPAM` | Disable the anti-spam checks from running on a form submission.               |

### Form question

| Field  | Type                                     | Description                                      | Example              |
| ------ | ---------------------------------------- | ------------------------------------------------ | -------------------- |
| `id`   | string                                   | Unique identifier of the question                | `"aabbcc"`           |
| `name` | string                                   | Name of the question                             | `"What's the time?"` |
| `type` | one of [Question types](#Question_types) | The type of input for this question              | `"radio"`            |
| `data` | [Question specific data](#Question_data) | Any specific data for the question type selected | Documented below     |

#### Question types

| Name         | Description                                               |
| ------------ | --------------------------------------------------------- |
| `radio`      | Radio buttons                                             |
| `checkbox`   | Checkbox toggle                                           |
| `select`     | Dropdown list                                             |
| `short_text` | One line input field                                      |
| `textarea`   | Long text input                                           |
| `code`       | Syntax highlighted code input                             |
| `range`      | Horizontal drag slider                                    |
| `section`    | Not an input, just a section of text to explain something |

#### Question data

Different questions require different input data to render. All data is in an object with keys and values as defined in the below tables. **All fields are required unless stated otherwise**.

##### `radio`

```js
{
    // Option list for radio buttons
    "options": [
        "Spam",
        "Eggs",
        "Ham"
    ]
}
```

##### `checkbox`

Checkboxes require no additional configuration

##### `select`

```js
{
    // Option list for select dropdown
    "options": [
        "United Kingdom",
        "United States"
    ]
}
```

##### `short_text`

Short text fields require no additional configuration.

##### `textarea`

Textareas require no additional configuration.

##### `code`

```js
{
    // A supported language from https://prismjs.com/#supported-languages
    "language": "python"
}
```

##### `range`

```js
{
    // A list of options to put on the range, from left to right
    "options": [
        "Not at all",
        "Not much",
        "A little",
        "A lot"
    ]
}
```

##### `section`

```js
{
    // OPTIONAL: Additional text to place below the section header
    "text": "This section will quiz you on A, B and C"
}
```
