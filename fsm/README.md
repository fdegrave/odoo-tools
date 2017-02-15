# Finite-State Machine

### A declarative Pythonic replacement for (simple) workflows

#### Transitions

This module provides the possibility to deal with the state transitions (and execute actions once a state is reached) in a declarative fashion. The system automatically triggers state transitions on odoo models based on conditions expressed under the form of boolean methods, either named `fsm_transition_[current_state]_[target_state]` or decorated with the "transition" decorator provided, with the argument `('[current_state]:[target_state]')` (several can be provided).

Hence, the following:

```python
def fsm_transition_draft_open(self):
    return self.toto()

def fsm_transition_draft_proforma(self):
    return self.toto()
```

Is equivalent to:

```python
from openerp.addons.fsm import fsm
    ...
    @fsm.transition('draft:open', 'draft:proforma')
    def toto(self):
        ...
```

If any transition condition is satisfied, the state transition is triggered (and no other transition condition is checked afterwards -- meaning the first condition verified determines the next state).

The system also allows one to easily **specify the groups that are authorized** to trigger a given transition as follows:

```python
from openerp.addons.fsm import fsm
    ...
    @fsm.transition('draft:open', 'draft:proforma', groups="account.group_account_manager")
    def toto(self):
        ...
```

This `groups` keyword argument is a string containing XML-IDs of `res.groups` instances, separated by a comma.

#### Actions

Once a new state is (automatically) reached, the field "state" is updated to reflect this change (no need to write the "state" field explicitely) and the method named `fsm_action_[new_state]` as well as all the methods decorated with the "action" decorator with the argument `('[new_state]')` are executed. For example, both the following methods are called once the 'open' state is reached:

```python
def fsm_action_open(self):
    ...

@fsm.action('open')
def foo(self):
    ...
```

This module also provides a "signal-like" system such that one can "send a signal" to a recordset using `recordset.fsm_send_signal('toto')` from anywhere in the code and check in the transition condition if the signal is received, using `self.fsm_get_signal('toto')`. Moreover, the standard workflow signals are overridden to send the FSM-signals as well, meaning that the standard "workflow" buttons can be used to trigger FSM-transitions.

Note that in order to work, the Odoo model under interest **must** have a `state` attribute of type `field.Selection`.

###Planned improvements
* Possibility to use other fields than `state` as nodes of the FSM (even several ones on the same object);
