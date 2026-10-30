# Approved arm modules

`direct`: make an audit judgment from the item packet.

`structured_claim_assumption_evidence`: enumerate the claim, explicit
assumptions, evidence, and the strongest justified conclusion before deciding.

`python_check`: if useful, run only deterministic calculations inside the
allocated sandbox; attach a tool receipt.

`lean_formal_check`: propose the narrowest formal target permitted by the item;
run only the pinned source environment; attach statement/proof hashes,
command, exit status, and stderr/stdout hashes.  Never infer empirical truth
from a successful check.

`countermodel_search`: seek an alternate model or parameter setting consistent
with allowed evidence that changes the conclusion; attach a witness or state
why no witness was found.

`evidence_audit`, `domain_audit`, and `numerical_check`: use only the unit
evidence allow-list.  `semantic_alignment_record` explicitly compares natural
claim, observable mapping, assumptions, and submitted Lean target.
