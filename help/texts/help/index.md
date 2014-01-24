<a name="what" class="anchor-fix"></a>
### What is this?

At *Joltem* ( short for “jolt them” ) our goal is to create a place that allows programmers to spontaneously come together and work openly on the best startup ideas. 

We believe the current process of forming companies is outdated. Our founding principle is that working openly can be a pivotal advantage for a young startup.

##### Building a team

In order to pursue most ideas you are going need a partner or two. On our platform you can post your idea, share the idea with anybody willing to listen, and begin collaborating on it immediately. 

If others find the idea interesting they can join you in making it a reality, in return they [receive an ownership stake](#impact) in the company. Essentially you allow people to invest in your company with their work.

##### Raising investment

Most of the money raised by early stage startups goes to hiring a team. This is a risky proposition for venture capitalists so they either must take a large stake in the company or close the door on a lot of projects.

However, if  you build your team openly and they are compensated with ownership raising capital can either be postponed or avoided completely. Best of all you won’t need anyone's permission to pursue your idea.

More so, we believe having ownership concentrated amongst the people directly working on the product gives you the best chance to succeed and if you manage to prove something raising capital will be a lot cheaper.

##### Hiring people

Once your company reaches a certain scale or if you simply have some task that needs specialized expertise you are going to need to hire people. 

The conventional way of hiring people is an extremely difficult process to navigate, especially for a young startup. Individuals with impressive resumes are mostly employed in comfortable positions, so most of the time you are left to sort a stack of questionable resumes hoping to find a diamond in the rough.

In an open company hiring is completely natural, you can freely broadcast ( job boards, freelance sites, etc. ) work that you want done on and the amount you are willing to pay. Anyone who is willing and capable may complete the work, without either of you wasting time reading a resume. If the company grows you can refer back and attempt to hire the best contributors as employees

Furthermore, with an open model you have a better chance of attracting the most talented people. If they believe in your organization and find your vision compelling, they might be willing to contribute in their spare time to specific tasks they may find interesting.

---

<a name="impact" class="anchor-fix"></a>
#### What is impact?

To track each user's continuous contribution to a project we use a metric called **impact**. 

Overtime accumulated **impact** will be [exchanged for equity](#exchange) in the company. The value of impact is backed by the work of the contributors and is determined through the [review and bargain process](#review).

<a name="exchange" class="anchor-fix"></a>
#### How is impact exchanged for equity?

Impact will always be backed by a pool of company stock, like an employee pool in regular companies. As work is completed on the project, users will accumulate impact through the review process. The impact the user accumulates is treated as the contribution he or she has made to creating the company. The **total impact**, a sum of all the impacts accumulated by all the users on the project, can be viewed as the total contribution to get the project to that particular state.

Periodically users will be able to exchange a portion of their impact for equity in the company, this is analogous to a vesting plan. The **exchange rate** is determined by dividing the size of the remaining backing stock pool by the total non-exchanged impact at the time of the exchange event. 

The periodicity of the exchange events rewards people who accumulated the most impact earliest in the project’s development by allowing them to exchange at higher rates. 

At any point the company’s board, which is initially just the founders, can decide to exchange the remaining backing pool at the current exchange rate or to allocate more stock for the backing pool. If the board decides on any action that may lower the value of the backing pool, such as a financing round or allocating stock to hire regular employees, they must file a proposition with the project participants and have them approve it.


<a name="review" class="anchor-fix"></a>
#### How does the review and bargain process work?

The review & bargain process is used for determing the value of each contribution. It is also meant to be a mechanism to promptly surface potential conflicts so that they may be resolved. 

After a contributor completes a solution they determine a fair amount for their contribution and they submit it along with the solution for review by the other contributors.

The other contributors determine whether the solution is satisfactory and whether the evaluation for the work is fair. If the evaluation is determined to be unreasonable by the other contributors, a bargaining process follows to determine the value of the contribution.

As long as people want to keep working with each other, the bargaining process will allow them to resolve any compensation and quality control issues. 

---

<a name="task-solutions" class="anchor-fix"></a>
#### What are tasks and solutions?

A **task** is a description of work, while a **solution** represents work or an intent to execute some work.

Tasks are proposed and curated through a process similar to [Python’s PEP system](http://en.wikipedia.org/wiki/Python_Enhancement_Proposal#Development), once approved solutions are solicited publicly using an open allocation model.

Each task may receive multiple solutions by anyone who is willing to contribute. Each solution may contain its own set of tasks, allowing for recursive delegation of work.

Each solutions is designated a branch name in each repository of the project and only the initiator of the solution has push access to that particular branch. 

As solutions are completed, the initiator of the parent task has the responsibility of merging in the work into the branch that initiated the task. This is similar to concepts in parallel computing where tasks are performed by individual components then later reduced into a cohesive solution.

On completion of a solution, a peer review is initiated to evaluate the completed work.

<a name="ratio" class="anchor-fix"></a>
#### What is the votes ratio?

The **votes ratio** is meant to couple reviewing with earning of impact. 

Roughly speaking it is a simple ratio of the *number of votes you have cast on other people’s solutions* over the *number you have received on your solutions* in the project with a few caps and modifications. For more detailed description of the rational behind this look at the [Voter Rational](http://joltem.com/joltem/task/45/) task and the [current live solution](http://joltem.com/joltem/solution/48/).

If your votes ratio drops below a certain threshold you are still able to earn impact, however the impact you earn will be withheld until the votes ratio is raised back up again.

---

<a name="idea" class="anchor-fix"></a>
#### Have an idea?

In the *alpha* stage the only project available is the *Joltem* project itself. However, in the near future, this will be a place where anybody will be able to broadcast their idea, work openly, and attract collaborators to bring the idea to reality. 

If you have an idea or you are part of an existing startup that would like to work openly on our platform contact us at <support@joltem.com> with a description of the idea.


---

<a name="company" class="anchor-fix"></a>
#### How is Joltem structured?

The *Joltem* project itself is a proof of concept, an open company. 

The company will be structured with *85%* of company's equity backing impact, the other *15%* is reserved for [Emil Davtyan](http://joltem.com/user/emil/) the founder and angel investor of the company.

Annually on the anniversary of the public release of the site *25%* of non-exchanged impact will be available to exchange for equity.


<a name="involved" class="anchor-fix"></a>
#### How to get involved?

You can follow our work without signing up, but if you want to contribute code or comment you will need to sign up.

To contribute code :

1. Sign up.
2. Add a SSH key in *Account > Keys*, so you can clone the repository.
3. Clone the repository.
4. Read the `README.md` document, on how to setup the code for local development ( we use [Vagrant](http://www.vagrantup.com) ).
5. Post a solution to one of the open tasks.
6. Rinse and repeat.

If you experience a problem contact the development team at <dev@joltem.com> and someone will respond promptly.

---

<a name="press" class="anchor-fix"></a>
#### We like the press.

Writing a story about us?

We will be happy to answer your questions, provide media, and talk your ear off about why what we are doing is important.

<press@joltem.com>



<a name="support" class="anchor-fix"></a>
#### We listen & help.

If you have other questions or suggestions.

<support@joltem.com>




