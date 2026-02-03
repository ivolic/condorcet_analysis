Empirical Analysis of RCV

We propose to continue a line of inquiry we began in the RCV project concerning Condorcet methods. We presented extensive results in our previous report; many of these results provide an opportunity for deeper analysis. Broadly, our goal is to evaluate whether Condorcet methods live up to the claims made by their advocates once realistic voting behavior is taken into account. For example, when voters cast truncated ballots or engage in common strategic behaviors such as burying, do Condorcet methods retain meaningful advantages over IRV?
 
In our previous project we analyzed several Condorcet methods. Under this proposal, we will continue to look at those methods but also incorporate two other ones that have received significant attention from prominent scholars, including Ned Foley and Eric Maskin: Total Vote Runoff and Diversity Score. To our knowledge, neither method has been rigorously studied under conditions that reflect realistic ballot truncation and strategic voting. The proposed project addresses this gap.
 
Specifically, we will pursue the following lines of analysis:
We will study the extent to which either Condorcet method performs similarly to IRV under various levels of ballot truncation.
We will analyze how susceptible Condorcet methods are to various forms of strategic voting such as burying, compromise voting, etc.
In our previous work, we did not pay attention to how various versions of Condorcet methods behave when there is no Condorcet winner, i.e. when there is a Condorcet cycle (which is the only way they differ). We will try to tease out these differences (for example, finding profiles where minimax has strategic voting but ranked pairs does not). These methods use margin graphs to determine how a cycle is broken, so applying some graph theory to these situations might provide interesting insights into whether graph-theoretic techniques can illuminate strategic voting.
Total Vote Runoff is based on the Borda scoring rule, and therefore the presence of partial ballots is a complication for this method. When voters cast short ballots, there are several ways one could choose to adapt Borda scoring to these incomplete preferences, and each choice could lead to methods which produce very different results in the context of strategic voting. We will use several different natural adaptations of the Borda rule to investigate if this choice matters or if we do not need to worry about how Total Vote Runoff handles partial ballots.
Eric Maskin’s Diversity Score hinges on imposing a threshold value for how far the electorate’s preferences deviate from being single-peaked. We would like to smooth this out and study the robustness of Diversity Score across various thresholds.
We will quantify the extent to which various voting strategies are successful for the voting blocs implementing them, versus when the implemented strategy achieves no effect or actually backfires on the voting bloc. We would also like to test a probabilistic rather than all-or-nothing approach to the strategic voting algorithms. This means that, when we currently model truncation, we truncate all ballots in a block, but one could instead have each voter in a bloc truncate with some probability.
We would also like to look at truncation coordination (or coordination for other behaviors) among the candidates. None of our previous algorithms did that, but it might happen under Condorcet. (For example, in the 2022 Alaska election, Palin and Peltola might have both encouraged their supporters to bullet vote because they realized they would not be the Condorcet winner.)
Much of the recent work surrounding Condorcet methods concerns the tendency of these methods to elect candidates with maximal utility, a notion imported from classical economics. Condorcet advocates point out that in theoretically ideal conditions, Condorcet methods elect the candidate with maximal utility more often than IRV. We will examine how well this analysis holds up when we introduce partial ballots and strategic voting.
 
As before, our analysis of Condorcet methods will be comparative, running in parallel with IRV (and possibly other methods). The empirical portion will be even more expansive since we recently got a hold of 900 additional multi-winner IRV elections from Australia, bringing the total of real-world political elections available to us to almost 3,000.


Research questions:

Is it Condor”say” or Condor”set”? Or Condor-ket?
Who benefits more from strategic voting? In particular, if I recall correctly Maskin claims the diversity score method is virtually resistant to strategic voting when preferences are single-peaked. We could test this in the context of partial ballots or whatever.
Realistic behavior for truncation/burying (10%, 20%, etc…)?
Redo the burying analysis for these two methods.
Could also say that we’ll do some initial STAR analysis near the end of the project.
Voter models specifically designed to create winner cycles so we can compare/contrast condorcet methods better
How sensitive is the diversity score method to the choice of threshold? How sensitive is the total runoff method to the choice of underlying Borda method?
How might candidates behave under a total runoff or diversity score system, and how might this affect the results?
Social utility analysis. How often do these methods choose the candidate of maximal/minimal utility? I suppose we should just restrict to the case when there’s a cycle. Unfortunately, for this piece we can’t use real preference profiles since we have no spatial info. Maybe use the CES stuff again, but this time something 2-D as well?
What happens when candidate encourage a certain type of voter behavior and a large proportion of their voters listen to them?
Because Total Vote Runoff is a sequential elimination procedure, it fails criteria like monotonicity. We could look for frequency of violations, and compare to IRV.
How do clones affect these two methods? I would guess not much for the diversity score method, but since Total Vote Runoff is based on Borda scores, might it be affected?
Investigate coalitional manipulation of the two methods? For Baldwin, maybe a coalition of voters boosts a weak candidate they don’t care about and buries the main threat to their favorite candidates?
More broadly, Baldwin is built on Borda scoring, and we know the Borda count is highly manipulable. How does this affect how Baldwin works? What issues of Borda transfer over? Since Baldwin is a Condorcet method (at least, if we use Borda AVG it is) then it should be more resistant to the spoiler effect than Borda.
