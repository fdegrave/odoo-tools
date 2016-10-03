# Finite-State Machine

### A declarative Pythonic replacement for (simple) workflows

This module provides the possibility to deal with the states transitions (and execute actions once a state is reached) in a declarative fashion. The system automatically triggers state transitions on odoo models based on conditions expressed under the form of methods, either named `fsm_transition_[current_state]_[target_state]` or decorated with the "transition" decorator provided, with the argument `('[current_state]:[target_state]')` (several can be provided).

Hence, the following:
    def fsm_transition_draft_open(self):
        return self.toto()
    
    def fsm_transition_draft_proforma(self):
        return self.toto()

Is equivalent to:
    from openerp.addons.fsm import fsm
    @fsm.transition('draft:open', 'draft:proforma')
        def toto(self):
            ...

If any transition condition is satisfied, the state transition is triggered (and no other transition condition is checked afterwards -- meaning the first condition verified determines the next state to reach).

Once a new state is (automatically) reached, the field "state" is updated to reflect this change and the method named
`fsm_action_[new_state]` as well as all the methods decorated with the "action" decorator with the argument `('[new_state]')` are called. For example, both the following methods are called once the 'open' state is reached:
    def fsm_action_open(self):
        ...
    
    @fsm.action('open')
    def foo(self):
        ...

There is also a "signal-like" system, where you can "send a signal" to a recordset using `recordset.fsm_send_signal('toto')` and then check in the transition condition `self.fsm_get_signal('toto')`. Moreover, one can use the standard workflow signals -- and thus the "signal" buttons in views -- to send the FSM-signals.