# A practical guide to investing, for the kids

## The Goal
To provide my children with data and visualizations to aid in understanding the concept of financial growth over time, and investing specifically. This will include the creation and use of an actual "investment vehicle" for each of the children (Child A and Child B), allowing them to balance immediate desire vs longer-term growth. In other words, I want to provide both a theoretical understanding of, and practical experience with, investings, in a way that prepares them to manage their own finances effectively, with a long-term view, as adults.

## Implementation vision
Note: this vision represents an initial concept, and can be modified as we go.

### Frontend
I want to build a local-only streamlit app that serves two primary purposes:
1. Contains theoretical instruction on investment and exponential growth over time. I expect this to be fairly simple, starting at least with a plot and table of exponential growth, including user inputs for starting funds, return rate, and duration.
2. A UI to manage "investment accounts" for each child. These represent actual accounts that I am funding, though the "accounts" for the purpose of this project are really just an accounting tool, and I don't need this project to actually manage any funds. 
- Starting with an initial "seed" balance, I want to maintain these in "real time", likely with daily compounding.
- I want a "balance history" to help in seeing the progress of growth. I want clean user inputs for "transactions", including both withdrawals and deposits. 
- When used, these inputs should immediately update the backend account record.
- In the backend, I want the ability to set the growth rate, with this rate displaying in the UI.
- The children's accounts do not need to be "firewalled" from each other. In fact, I see it being beneficial for them to see how each other is doing when considering their own investment "strategy".

# Technical considerations
- This project will be a git repo, published privately to my Github account
- This project should be written predominantly, if not exclusively, in python
- UV will be used for venv management. Always run `source ~/project/investing_for_kids/.venv/bin/activate` when initializing a shell.
- Use ruff formatting
- I am open to suggestions on solutions for storing and fetching account information. The simplest would be a csv file, though perhaps a more robust framework would be preferred. But then something like a local postgres db is probably overkill. I also want to ensure this information is sufficiently backed up, perhaps github versioning is sufficient for that.
- In technical implementation, consider that this is a private project, with no other codeowners or users. Keep this in mind when writing type validations, testing, etc.
- I am relatively new to using Claude Code. Please suggest any MCPs (such as Playwright), skills, or other tips for developing. Also, feel free to provide suggestions on claude settings.
- Note on documentation and doc strings: Provide clear but concise documentation, such as docstrings for functions. Limit use of #comments within functions.
- I want the python code built herein to be loadable as a package, with a clear functional layout.
