# Forms Schema

Since MongoDB has no set schema, we document it here to document what our objects should look like. If you add new properties or remove them from objects **make sure to update them here**.

In this document:
- [Form](#form)
    - [Form features](#form-features)
    - [Form question](#form-question)
- [Form response](#form-response)
    - [User details object](#user-details-object)
    - [Anti-spam object](#anti-spam-object)

## Form

| Field              | Type                                     | Description                                                                                                      | Example                                        |
|--------------------|------------------------------------------|------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| `id`               | Unique identifier                        | A user selected, unique, descriptive identifier (used in URL routes, so no spaces)                               | `"ban-appeals"`                                |
| `features`         | List of [form features](#form-features)  | A list of features to change the behaviour of the form, described in the features section                        | `["OPEN", "COLLECT_EMAIL"]`                    |
| `questions`        | List of [form questions](#form-question) | The list of questions to render on a specific form                                                               | Too long! See below                            |
| `name`             | String                                   | Name of the form                                                                                                 | `"Summer Code Jam 2100"`                       |
| `description`      | String                                   | Form description                                                                                                 | `"This is my amazing form description."`       |
| `webhook`          | [Webhook object](#webhooks)              | An optional discord webhook.                                                                                     | See webhook documentation.                     |
| `submitted_text`   | Optional[String]                         | An optional string for the response upon submitting.                                                             | `"This is my amazing form response."`          |
| `discord_role`     | String (optional)                        | Discord role ID what will be assigned, required when `ASSIGN_ROLE` flag provided.                                | `784467518298259466`                           |
| `response_readers` | List[String]                             | Discord roles which can view the responses of the form. Can not be the everyone role.                            | `["267629731250176001", "825337057181696020"]` |
| `editors`          | List[String]                             | Discord roles which have permission to edit, delete, or otherwise modify the form. Can not be the everyone role. | `["409416496733880320"]`                       |


### Form features

| Flag               | Description                                                                   |
|--------------------|-------------------------------------------------------------------------------|
| `DISCOVERABLE`     | The form should be displayed on the homepage of the forms application.        |
| `REQUIRES_LOGIN`   | Requires the user to authenticate with Discord before completing the form.    |
| `OPEN`             | The form is currently accepting responses.                                    |
| `COLLECT_EMAIL`    | The form should collect the email from submissions. Requires `REQUIRES_LOGIN` |
| `DISABLE_ANTISPAM` | Disable the anti-spam checks from running on a form submission.               |
| `WEBHOOK_ENABLED`  | The form should notify the webhook. Has no effect if no webhook is set.       |
| `ASSIGN_ROLE`      | The form should assign role to user. Requires `REQUIRES_LOGIN`.               |

### Webhooks
Discord webhooks to send information upon form submission.

| Field     | Type   | Description                                                                                               |
|-----------|--------|-----------------------------------------------------------------------------------------------------------|
| `url`     | String | Discord webhook URL.                                                                                      |
| `message` | String | An optional message to include before the embed. Can use certain [context variables](#webhook-variables). |


#### Webhook Variables
The following variables can be used in a webhook's message. The variables must be wrapped by braces (`{}`).

| Name          | Description                                                                  |
|---------------|------------------------------------------------------------------------------|
| `user`        | A discord mention of the user submitting the form, or "User" if unavailable. |
| `response_id` | ID of the submitted response.                                                |
| `form`        | Name of the submitted form.                                                  |
| `form_id`     | ID of the submitted form.                                                    |
| `time`        | ISO submission timestamp.                                                    |


### Form question

| Field      | Type                                     | Description                                      | Example              |
|------------|------------------------------------------|--------------------------------------------------|----------------------|
| `id`       | string                                   | Unique identifier of the question                | `"aabbcc"`           |
| `name`     | string                                   | Name of the question                             | `"What's the time?"` |
| `type`     | one of [Question types](#question-types) | The type of input for this question              | `"radio"`            |
| `data`     | [Question specific data](#question-data) | Any specific data for the question type selected | Documented below     |
| `required` | Boolean                                  | Indicates whether the field must be filled       | `True`               |

#### Question types

| Name         | Description                                                       |
|--------------|-------------------------------------------------------------------|
| `radio`      | Radio buttons                                                     |
| `checkbox`   | Checkbox toggle                                                   |
| `select`     | Dropdown list                                                     |
| `short_text` | One line input field                                              |
| `textarea`   | Long text input                                                   |
| `code`       | Syntax highlighted code input                                     |
| `range`      | Horizontal drag slider                                            |
| `section`    | Not an input, just a section of text to explain something         |
| `timezone`   | Similar to select, attempts to automatically detect user timezone |

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

##### `checkbox`

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
    "language": "python",
    // An optinal mapping of unit tests
    "unittests": {
        // Record a submission, even if the tests don't pass
        // Default: false
        "allow_failure": false,
        "tests": {
            "unit_1": "unit_code()",
            ...
        }
    }
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

##### `timezone`

Timezones require no additional options, they will automatically attempt to
select the users timezone, or allow the user to select one if it is detected
wrong/could not be detected.

## Form response

| Field       | Type                                                 | Description                                                                 |
|-------------|------------------------------------------------------|-----------------------------------------------------------------------------|
| `_id`/`id`  | MongoDB ObjectID                                     | Random identifier used for the response                                     |
| `user`      | Optional [user details object](#user-details-object) | An object describing the user that submitted if the form is not anonymous   |
| `antispam`  | Optional [anti spam object](#anti-spam-object)       | An object containing information about the anti-spam on the form submission |
| `response`  | Object                                               | Object containing question IDs mapping to the users answer*                 |
| `form_id`   | String                                               | ID of the form that the user is submitting to                               |
| `timestamp` | String                                               | ISO formatted string of submission time.                                    |


&nbsp;* If the question is of type `code`, the response has the following structure:
```json
"response": {
  "<QUESTION ID>": {
    "value": "<USER CODE>",
    "passed": bool,
    "failures": ["<TEST NAME 1>", "<TEST NAME 4>", "<HIDDEN TEST 1>", ...]
  },
  ...
}
```
* Values in `<>` are placeholders, while the rest are actual keys
* `passed` is True only if all tests in the suite passed.

### User details object

The user details contains the information returned by Discord alongside an `admin` boolean key representing that the user has admin privileges. The information returned from Discord can be found in the [Discord Developer portal](https://discord.com/developers/docs/resources/user#user-object).

### Anti-spam object

The anti-spam object contains information about the source of the form submission.

| Field             | Type    | Description                                     |
|-------------------|---------|-------------------------------------------------|
| `ip_hash`         | String  | hash of the submitting users IP address         |
| `user_agent_hash` | String  | hash of the submitting users user agent         |
| `captcha_pass`    | Boolean | Whether the user passsed the hCaptcha           |
| `dns_blacklisted` | Boolean | Whether the submitting IP is on a DNS blacklist |
