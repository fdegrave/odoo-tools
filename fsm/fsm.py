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
from odoo import models, api
from inspect import getmembers


def transition(*args, **kwargs):
    """Decorator that adds a '_fsm_transitions' attribute to the method containing the list of state transitions for
    which this method is a condition
    """
    def inner(method):
        if 'groups' in kwargs:
            def group_decorator(self, *a, **kw):
                groups = [self.env.ref(g.strip()) for g in kwargs['groups'].split(',')]
                if any(self.env.user in gr.users for gr in groups):
                    return method(self, *a, **kw)
                return False
            group_decorator._fsm_transitions = args
            return group_decorator
        else:
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
    return [m for m in set(methods)]


def _trigger_actions(self, state):
    actions = _get_methods(self, "_fsm_actions", state)
    actions.append(getattr(type(self), "fsm_action_%s" % state, lambda *a: None))
    for act in actions:
        act(self)


def _trigger_state_transition(self):
    """Triggers a state transition if the test is successful, then executes the actions of the new state"""
    if self._context.get('no_state_trigger'):
        return
    if 'state' in self._fields and self._fields['state'].type == "selection":
        for target_state in [r[0] for r in self._fields['state']._description_selection(self.env)
                             if r[0] != self.state]:
            methods = filter(None, [getattr(type(self), "fsm_transition_%s_%s" % (self.state, target_state), None)] +
                             _get_methods(self, "_fsm_transitions", "%s:%s" % (self.state, target_state)))
            if any(meth(self) for meth in methods):
                self.with_context(no_state_trigger=True).state = target_state
                _trigger_actions(self, target_state)
                break


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.multi
    def _write(self, vals):
        """Override the write method to trigger the state transition"""
        res = super(Base, self)._write(vals)
        for rec in self:
            _trigger_state_transition(rec)
        return res

    @api.model
    def create(self, vals):
        """Override the create method to trigger the state transition"""
        res = super(Base, self).create(vals)
        if 'state' in res._fields:
            _trigger_actions(res, res.state)  # action on the starting state
        _trigger_state_transition(res)
        return res

    def signal_workflow(self, signal):
        """Override the signal_workflow to send a 'fsm signal' as well"""
        res = super(Base, self).signal_workflow(signal)
        self.fsm_send_signal(signal)
        return res

    @api.multi
    def fsm_send_signal(self, signal):
        """Trigger state transition with a 'fsm_signal_' + model name context key"""
        for rec in self:
            _trigger_state_transition(rec.with_context({'fsm_signal_' + self._name: signal}))

    @api.multi
    def fsm_get_signal(self, signal):
        """Just check if the context contains a key 'fsm_signal_' + model name with a value == `signal`"""
        return self._context.get('fsm_signal_' + self._name) == signal
