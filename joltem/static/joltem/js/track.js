/**
 * For tracking with Google analytics.
 *
 * Contains utility functions for tracking various events.
 *
 */

// STANDARD ANALYTICS CODE, DON'T MODIFY ///////////////////////////////////////
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', 'UA-487998-17', 'joltem.com');
ga('send', 'pageview');
////////////////////////////////////////////////////////////////////////////////

TRACK = {
    _track_event: function (category, action, label, value, non_interaction){
        console.log("TRACK EVENT :"
            +" / Category : "+category
            +" / Action : "+action
            +" / Label : "+label
        );
        ga('send', 'event', category, action, label, value,
            {'nonInteraction': non_interaction});
    },
    users: {
        category : "Users",
        sign_up : function (label){
            TRACK._track_event(this.category, "Sign Up", label, 0, false);
        }
    },
    project: {
        category : "Projects",
        create : function (label){
            TRACK._track_event(this.category, "Create", label, 0, false);
        },
        edit : function (label){
            TRACK._track_event(this.category, "Edit", label, 0, false);
        }
    },
    repository: {
        category : "Repositories",
        create : function (label){
            TRACK._track_event(this.category, "Create", label, 0, false);
        }
    },
    task: {
        category : "Tasks",
        create : function (label){
            TRACK._track_event(this.category, "Create", label, 0, false);
        },
        close : function (label){
            TRACK._track_event(this.category, "Close", label, 0, false);
        },
        reopen : function (label){
            TRACK._track_event(this.category, "Reopen", label, 0, false);
        },
        accept : function (label){
            TRACK._track_event(this.category, "Accept", label, 0, false);
        },
        reject : function (label){
            TRACK._track_event(this.category, "Reject", label, 0, false);
        },
        edit : function (label){
            TRACK._track_event(this.category, "Edit", label, 0, false);
        }
    },
    solution: {
        category: "Solution",
        create : function (label){
            TRACK._track_event(this.category, "Create", label, 0, false);
        },
        close : function (label){
            TRACK._track_event(this.category, "Close", label, 0, false);
        },
        reopen : function (label){
            TRACK._track_event(this.category, "Reopen", label, 0, false);
        },
        complete : function (label){
            TRACK._track_event(this.category, "Complete", label, 0, false);
        },
        incomplete : function (label){
            TRACK._track_event(this.category, "Incomplete", label, 0, false);
        },
        edit : function (label){
            TRACK._track_event(this.category, "Edit", label, 0, false);
        }
    }
}

