# -*- coding: utf-8 -*-
##############################################################################
#
#    UNamur - University of Namur, Belgium
#    Copyright (C) UNamur <http://www.unamur.be>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api
from inspect import getmembers


def transition(*args):
    """Decorator that adds a '_fsm_transitions' attribute to the method containing the list of state transitions for
    which this method is a condition
    """
    def inner(method):
        method._fsm_transitions = args
        return method
    return inner


def action(*args):
    """Decorator that adds a '_fsm_actions' attribute to the method containing the list of states that trigger this
    method execution
    """
    def inner(method):
        method._fsm_actions = args
        return method
    return inner


def _get_methods(self, attribute, value):
    """Return all the methods with `value` being a member of `attribute`"""
    def has_attribute(func):
        return callable(func) and hasattr(func, attribute) and value in getattr(func, attribute, [])

    cls = type(self)
    methods = []
    for _attr, func in getmembers(cls, has_attribute):
        methods.append(func)
    return methods


def _trigger_actions(self, state):
    actions = _get_methods(self, "_fsm_actions", state)
    actions.append(getattr(self, "fsm_action_%s" % state, lambda *a: None))
    for act in actions:
        act(self)


def _trigger_state_transition(self):
    """Triggers a state transition if the test is successful, then executes the actions of the new state"""
    if self._context.get('no_state_trigger'):
        return
    if 'state' in self._fields and self._fields['state'].type == "selection":
        for target_state in [r[0] for r in self._fields['state']._description_selection(self.env)
                             if r[0] != self.state]:
            methods = filter(None, [getattr(self, "fsm_transition_%s_%s" % (self.state, target_state), None)] +
                             _get_methods(self, "_fsm_transitions", "%s:%s" % (self.state, target_state)))
            if any(meth(self) for meth in methods):
                self.with_context(no_state_trigger=True).state = target_state
                _trigger_actions(self, target_state)
                break


@api.multi
def write(recset, vals):
    """Patching of the write method to trigger the state transition"""
    res = write.origin(recset, vals)
    for rec in recset:
        _trigger_state_transition(rec)
    return res

models.BaseModel._patch_method("write", write)


@api.model
def create(recset, vals):
    """Patching of the create method to trigger the state transition"""
    res = create.origin(recset, vals)
    if 'state' in res._fields:
        _trigger_actions(res, res.state)  # action on the starting state
    _trigger_state_transition(res)
    return res

models.BaseModel._patch_method("create", create)


def signal_workflow(self, cr, uid, ids, signal, context=None):
    """Patching of the signal_workflow to send a 'fsm signal' as well"""
    res = signal_workflow.origin(self, cr, uid, ids, signal, context=context)
    recset = self.browse(cr, uid, ids)
    fsm_send_signal(recset, signal)
    return res

models.BaseModel._patch_method("signal_workflow", signal_workflow)


@api.multi
def fsm_send_signal(recset, signal):
    """Trigger state transition with a 'fsm_signal_' + model name context key"""
    for rec in recset:
        _trigger_state_transition(rec.with_context({'fsm_signal_' + recset._name: signal}))

models.BaseModel.fsm_send_signal = fsm_send_signal


@api.multi
def fsm_get_signal(recset, signal):
    """Just check if the context contains a key 'fsm_signal_' + model name with a value == `signal`"""
    return recset._context.get('fsm_signal_' + recset._name) == signal

models.BaseModel.fsm_get_signal = fsm_get_signal
