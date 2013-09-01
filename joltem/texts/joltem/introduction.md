###Welcome to the team. Let's get started.
This is a brief intoduction to get you accustomed with the site and how we work.

####How we work?

Work is completed through **tasks** and **solutions**, so lets define what they are :

* A **task** contains a description of work and represents an intent to administrate the work.
* A **solution** represents work or an intent to execute some work.

Anybody can create tasks and solutions at any **level** ( correspond to development branches ), but tasks require acceptance from an **adminstrator** of a parent level.

####How peer review works?

**Impact** is earned through a continous peer review of solutions and comments.

The voting system uses a *logarithmic scale* and weighs votes by the voter's impact. When voting your decision will be to determine whether the contribution is a *10*, *100*, *10^3*, … or *10^6*. Votes above *10* require justification from the other votes to count.

A vote of 0 represents unsatisfaction, and in case of solutions requires a comment to count. If there are too many unsatisfactory votes the user won't receive impact from the contribution, despite the other votes.

The peer review system is crucial to the health of the system, so it is important we get feedback and debate tweaks and alternatives. If you have a suggestion leave a comment on the [current live solution](http://joltem.com/joltem/solution/1/) or create your own solution on the [*Determining Impact* task](http://joltem.com/joltem/task/6/).

####How to get started?

*Process for setting up :*

1. Add a SSH key to the system so you may pull and push from the repositories.
2. Clone the main repository : `git clone git@joltem.com:joltem/main`
3. Refer to the `README.md` for instructions on how to setup the system in your development environment.

*Process for contributing a solution :*

1. Look at list of open tasks and open a solution to one. Or suggest a solution to another solution.
2. Checkout and push to designated branch for the solution, from the appropriate parent. Solution branches are named `s/{solution_id}` and only the solution owner can push to them.
3. If you complete the solution mark it complete to send it to review, if not mark it closed to indicate it is not being worked on anymore.
4. While in review you can mark incomplete and make revisions, and later mark it complete again to send it for review.

*Process for administrating a task :*

1. While working on a solution, you may open a task to solicit others to provide solutions for something you may need.
2. As solutions to your task are completed, it is your responsibility to merge the work into your solution.
3. Mark the task closed if you have received enough solutions or feel it is unnecessary. Don't worry if the task still has open solutions, they will become suggested solutions to a parent level.