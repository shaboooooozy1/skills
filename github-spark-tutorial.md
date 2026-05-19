# Building and deploying AI-powered apps with GitHub Spark

Learn how to build and deploy an intelligent web app with natural language using GitHub Spark.

> [!NOTE]
>
> * GitHub Spark is in public preview with [data protection](https://gh.io/dpa) and subject to change.
> * The GitHub Copilot setting that blocks suggestions matching public code may not work as intended when using Spark. See [Managing GitHub Copilot policies as an individual subscriber](/en/copilot/how-tos/manage-your-account/managing-copilot-policies-as-an-individual-subscriber#enabling-or-disabling-suggestions-matching-public-code).

## Introduction

With GitHub Spark, you can describe what you want in natural language and get a fullstack web app with data storage, AI features, and GitHub authentication built in. You can iterate using prompts, visual tools, or code, and then deploy with a click to a fully managed runtime.

Spark is seamlessly integrated with GitHub so you can develop your spark via a synced GitHub codespace with Copilot for advanced editing. You can also create a repository for team collaboration, and leverage GitHub's ecosystem of tools and integrations.

This tutorial will guide you through the full lifecycle of building and deploying an app with Spark and exploring its features.

### Prerequisites

* A GitHub account with Copilot Pro+ or Copilot Enterprise license.

## Step 1: Create your web app

For this tutorial, we'll create a simple marketing tool app, where:

* The user enters a description of a product they want to market.
* The app generates marketing copy, and recommends a visual strategy and target audience.

1. Navigate to <https://github.com/spark>.

2. In the input field, enter a description of your app. For example:

   ```copilot copy
   Build an app called "AI-Powered Marketing Assistant."

   The app should allow users to input a brief description of a product or service. When the user submits their brief, send this information to a generative AI model with a prompt that asks the AI to return the following:
      - Persuasive and engaging marketing copy for the product or service.
      - A visual strategy for how to present the product/service (e.g., suggested imagery, colors, design motifs, or mood).
      - A recommendation for the ideal target audience.
   The app should display these three elements clearly and in an organized manner.  The app should look modern, fresh and engaging.
   ```

   > [!TIP]
   >
   > * Be specific, and provide as many details as possible for the best results. You can ask [Copilot Chat](https://github.com/copilot?ref_product=copilot&ref_type=engagement&ref_style=text) to refine or suggest improvements to your initial prompt.
   > * Alternatively, drop a markdown document into the input field to provide Spark with more context on what you're hoping to build.

3. Optionally, upload an image to provide Spark with a visual reference for your app. Mocks, sketches, or screenshots all work to provide Spark with an idea of what you want to build.

4. Click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-paper-airplane" aria-label="Submit prompt" role="img"><path d="M.989 8 .064 2.68a1.342 1.342 0 0 1 1.85-1.462l13.402 5.744a1.13 1.13 0 0 1 0 2.076L1.913 14.782a1.343 1.343 0 0 1-1.85-1.463L.99 8Zm.603-5.288L2.38 7.25h4.87a.75.75 0 0 1 0 1.5H2.38l-.788 4.538L13.929 8Z"></path></svg>** to build your app.

   > [!NOTE]
   > Spark will always generate a Typescript and React app.

## Step 2: Refine and expand your app

Once Spark is done generating your app, you can test it out in the live preview window. From here, you can iterate on and expand your app using natural language, visual editing controls, or code.

1. To make changes to your app using **natural language**, under the "Iterate" tab in the left sidebar, enter your instructions in the main input field, then submit.
2. Optionally, click one of the "Suggestions" directly above the input field in the "Iterate" tab to develop your app.
3. Spark automatically alerts you to detected errors. To fix the errors, click **Fix All** above the input field in the "Iterate" tab.
4. Optionally, click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-code" aria-label="code" role="img"><path d="m11.28 3.22 4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734L13.94 8l-3.72-3.72a.749.749 0 0 1 .326-1.275.749.749 0 0 1 .734.215Zm-6.56 0a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L2.06 8l3.72 3.72a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L.47 8.53a.75.75 0 0 1 0-1.06Z"></path></svg> Code** to view and edit the underlying code. The code editing panel has Copilot inline suggestions built in.
5. To make targeted changes to a specific element of your app click the **target icon** in the top right corner then hover over and select an element in the live preview pane.

## Step 3: Customize the styling of your app

Next, let's change the styling of your app using Spark's built-in tools. Alternatively, you can edit the code directly.

1. Change your app's overall appearance:
   * Click the **Theme** tab to adjust typography, colors, border radius, spacing, and other visual elements.
   * Choose from pre-generated themes to easily update the overall style your app.

2. To target visual edits at a specific component, click the **target icon**, then select an element of the app in the preview pane. Styling controls related to that specific element will show up in the left sidebar.

3. Optionally, edit styles in code:
   * Click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-code" aria-label="Code" role="img"><path d="m11.28 3.22 4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734L13.94 8l-3.72-3.72a.749.749 0 0 1 .326-1.275.749.749 0 0 1 .734.215Zm-6.56 0a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L2.06 8l3.72 3.72a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L.47 8.53a.75.75 0 0 1 0-1.06Z"></path></svg>** to open the code editor.
   * Modify CSS, Tailwind CSS, or custom variables for fine-grained control (e.g., padding, spacing, fonts, colors).

     > [!TIP]
     > You can import custom fonts (like Google Fonts) or add advanced styles directly in the Spark code editor.
     > Ask [Copilot Chat](https://github.com/copilot?ref_product=copilot&ref_type=engagement&ref_style=text) for step-by-step guidance if you're not familiar with styling syntax.

4. Click the **Assets** tab to upload assets you want to surface in your app.
   * Add images, logos, videos, documents or other assets to personalize your app.
   * Once uploaded, instruct Spark on how you'd like to incorporate those assets into your app in the "Iterate" tab.

## Step 4: Store and manage data

If Spark detects the need to store data in your app, it will automatically set up data storage for you using a key-value store.

For our marketing app, let's add data storage so that users can save their favorite pieces of marketing copy and easily access them again later:

1. Use the following instruction in the "Iterate" tab to guide Spark:

   ```copilot copy
   Add a "Favorites" page where users can save and view their favorite marketing copy results.
   ```

2. Interact with the app once it's done generating to test saving and retrieving favorites.

3. Check the "Data" tab to view and edit the stored values.

4. If you explicitly **don't** want Spark to save data, ask Spark to "store data locally" or "don't persist data".

## Step 5: Refine AI capabilities

Next, let's iterate on the AI capabilities included in our app, which are powered by GitHub Models.

Spark automatically detects when AI is needed for features in your app. It will auto-generate the prompts for each AI feature, integrate with the best-fit models, and manage API integration and LLM inference on your behalf.

1. Click the **Prompts** tab.
2. Review the prompts Spark generated to power each of the AI features used in your app.
   * In the case of our marketing app there are three separate prompts Spark has generated for us (marketing copy generation, visual strategy recommendation, and target audience recommendation).
3. Click on each prompt to view and edit without needing to go into the code. Make adjustments to better fit your use case.
4. Test the app to see updated results.

## Step 6: Edit and debug with code and Copilot

You can view or edit your app’s code directly in Spark or via a synced GitHub codespace.

> [!NOTE]
>
> * Spark uses an opinionated stack (**React**, **TypeScript**) for reliability.
> * For best results, you should **work within Spark's SDK** and core framework.
> * You can **add external libraries**, but compatibility isn’t guaranteed — you should test thoroughly.
> * Directly editing the React code **lets you add model context**, as long as you follow valid syntax and Spark's framework.

1. To edit code in Spark:
   * Click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-code" aria-label="Code" role="img"><path d="m11.28 3.22 4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734L13.94 8l-3.72-3.72a.749.749 0 0 1 .326-1.275.749.749 0 0 1 .734.215Zm-6.56 0a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L2.06 8l3.72 3.72a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L.47 8.53a.75.75 0 0 1 0-1.06Z"></path></svg> Code**.
   * Navigate the file tree and make any edits, with access to Copilot inline suggestions in the editor. Changes are reflected instantly in the live preview window.
2. To make more advanced edits:
   * In the top right corner, click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-kebab-horizontal" aria-label="More actions" role="img"><path d="M8 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM1.5 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Zm13 0a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"></path></svg>**, then click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-codespaces" aria-label="codespaces icon" role="img"><path d="M0 11.25c0-.966.784-1.75 1.75-1.75h12.5c.966 0 1.75.784 1.75 1.75v3A1.75 1.75 0 0 1 14.25 16H1.75A1.75 1.75 0 0 1 0 14.25Zm2-9.5C2 .784 2.784 0 3.75 0h8.5C13.216 0 14 .784 14 1.75v5a1.75 1.75 0 0 1-1.75 1.75h-8.5A1.75 1.75 0 0 1 2 6.75Zm1.75-.25a.25.25 0 0 0-.25.25v5c0 .138.112.25.25.25h8.5a.25.25 0 0 0 .25-.25v-5a.25.25 0 0 0-.25-.25Zm-2 9.5a.25.25 0 0 0-.25.25v3c0 .138.112.25.25.25h12.5a.25.25 0 0 0 .25-.25v-3a.25.25 0 0 0-.25-.25Z"></path><path d="M7 12.75a.75.75 0 0 1 .75-.75h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1-.75-.75Zm-4 0a.75.75 0 0 1 .75-.75h.5a.75.75 0 0 1 0 1.5h-.5a.75.75 0 0 1-.75-.75Z"></path></svg> Open codespace** (a full-featured cloud IDE) to launch a codespace in a new browser tab.
   * Once inside the codespace, click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-copilot" aria-label="copilot" role="img"><path d="M7.998 15.035c-4.562 0-7.873-2.914-7.998-3.749V9.338c.085-.628.677-1.686 1.588-2.065.013-.07.024-.143.036-.218.029-.183.06-.384.126-.612-.201-.508-.254-1.084-.254-1.656 0-.87.128-1.769.693-2.484.579-.733 1.494-1.124 2.724-1.261 1.206-.134 2.262.034 2.944.765.05.053.096.108.139.165.044-.057.094-.112.143-.165.682-.731 1.738-.899 2.944-.765 1.23.137 2.145.528 2.724 1.261.566.715.693 1.614.693 2.484 0 .572-.053 1.148-.254 1.656.066.228.098.429.126.612.012.076.024.148.037.218.924.385 1.522 1.471 1.591 2.095v1.872c0 .766-3.351 3.795-8.002 3.795Zm0-1.485c2.28 0 4.584-1.11 5.002-1.433V7.862l-.023-.116c-.49.21-1.075.291-1.727.291-1.146 0-2.059-.327-2.71-.991A3.222 3.222 0 0 1 8 6.303a3.24 3.24 0 0 1-.544.743c-.65.664-1.563.991-2.71.991-.652 0-1.236-.081-1.727-.291l-.023.116v4.255c.419.323 2.722 1.433 5.002 1.433ZM6.762 2.83c-.193-.206-.637-.413-1.682-.297-1.019.113-1.479.404-1.713.7-.247.312-.369.789-.369 1.554 0 .793.129 1.171.308 1.371.162.181.519.379 1.442.379.853 0 1.339-.235 1.638-.54.315-.322.527-.827.617-1.553.117-.935-.037-1.395-.241-1.614Zm4.155-.297c-1.044-.116-1.488.091-1.681.297-.204.219-.359.679-.242 1.614.091.726.303 1.231.618 1.553.299.305.784.54 1.638.54.922 0 1.28-.198 1.442-.379.179-.2.308-.578.308-1.371 0-.765-.123-1.242-.37-1.554-.233-.296-.693-.587-1.713-.7Z"></path><path d="M6.25 9.037a.75.75 0 0 1 .75.75v1.501a.75.75 0 0 1-1.5 0V9.787a.75.75 0 0 1 .75-.75Zm4.25.75v1.501a.75.75 0 0 1-1.5 0V9.787a.75.75 0 0 1 1.5 0Z"></path></svg>** to open Copilot to make more advanced changes.
     * In the prompt box, select **Agent** mode to enable Copilot to autonomously build, review, and troubleshoot your code.
     * Select **Edit** mode for Copilot to review your app's code and suggest improvements and fixes.
     * Choose **Ask** mode for Copilot to explain and help you understand the code or any errors you see in Spark.
   * Changes you make in the codespace are automatically synced to Spark.

## Step 7: Deploy and share your app

Spark comes with a fully integrated runtime environment that allows you to deploy your app in one click.

> [!NOTE]
>
> * When you deploy your spark, if you choose to make it visible to other users, note that the data in your app is **shared across all users** who can access your app. Make sure no sensitive data is included in your spark prior to updating visibility settings.
> * You can also choose to share your spark as **read-only** so that other users can view your app's content, but they cannot edit content, delete files or records, or create new items.

1. In the top right corner, click **Publish**.

2. By default, your spark will be private and only accessible to you. Under "Visibility", choose whether you want your spark to remain private, or make it available to members of a specific organization on GitHub, or all GitHub users.

   ![Screenshot of the GitHub Spark publication menu. The "All GitHub users" visibility option is outlined in orange.](/assets/images/help/copilot/spark-github-user-visibility.png)

3. Under "Data Access", choose whether you want to give other users read-only or write access to your app.

   Choose **read-only** to let others view your app, without allowing them to create, edit or delete content.

   For example, if you've created a family calendar app and you want users to view the app but you don't want them to be able to create, edit or delete events, choose **read-only** so users can't modify your spark's data store.

4. Click **Visit site** to be taken to your live, deployed app. Copy your site's URL to share with others.

   When you publish your app, Spark automatically includes cloud-based storage and LLM inference for your application to use as part of the integrated runtime.

   The URL for your spark is generated based on the name of your spark. You can edit the name of your app and Spark will automatically manage re-routing of old URLs to your latest URL.

## Step 8: Invite collaborators with a repository

Now that you have a functional, deployed app, you can continue to build and collaborate on your app in the same way you would with any other GitHub project, by creating and linking a GitHub repository to your spark.

1. In the top right corner, click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-kebab-horizontal" aria-label="More actions" role="img"><path d="M8 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM1.5 9a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Zm13 0a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"></path></svg>**, then click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-repo-push" aria-label="repo-push" role="img"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0V1.5h-8a1 1 0 0 0-1 1v6.708A2.493 2.493 0 0 1 4.5 9h2.25a.75.75 0 0 1 0 1.5H4.5a1 1 0 0 0 0 2h4.75a.75.75 0 0 1 0 1.5H4.5A2.5 2.5 0 0 1 2 11.5Zm12.23 7.79h-.001l-1.224-1.224v6.184a.75.75 0 0 1-1.5 0V9.066L10.28 10.29a.75.75 0 0 1-1.06-1.061l2.505-2.504a.75.75 0 0 1 1.06 0L15.29 9.23a.751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018Z"></path></svg> Create repository**.
2. In dialog box that opens, click **Create**.

A new, private repository is created under your personal account on GitHub, with the name of the repository based on the name of your spark.

Any changes made to your spark prior to repository creation will be added to your repository so you have a full record of all changes and commits made to your spark since its creation.

There's a two-way sync between your spark and the repository, so changes made in either Spark or the main branch of your repository are automatically reflected in both places.

You can also create issues in your repository and assign them to Copilot cloud agent so it can draft pull requests for fixes and improvements.

## Next steps

Explore more ideas you can build with Spark:

* **Prototype new ideas quickly**: if you have a specific idea for a feature or app, upload a mockup, sketch, screenshot, or even paste a markdown documentation into Spark and ask Spark to build out your idea.
* **Build internal tools for yourself and your team**: If you have a common workflow or process that currently sits in a document or spreadsheet, explain your workflow or process to Spark and Spark can turn it into an interactive web app.

## Further reading

* [Responsible use of GitHub Spark](/en/copilot/responsible-use-of-github-copilot-features/responsible-use-of-github-spark)
* [GitHub Spark billing](/en/copilot/concepts/copilot-billing/about-billing-for-github-spark)
* [GitHub Pre-release License Terms](/en/site-policy/github-terms/github-pre-release-license-terms)
