Kv Evolution proposal
======================

To reviewers, please read the whole proposal (once all sections are complete), because although long and in depth, it does provide a full specification.

Following is a proposal for the evolution of kv, including it's integration into pure python and an associated compiler. For end users, writing kv code will seamlessly integrate into the rest of their python code, while automatically binding kv rules inline. To remove any ambiguity of where binding occurs and how to effect it, the goal of this project was to make binding syntactically clear, with the minimal amount of line noise and to remove any ambiguity in how kv rules are applied - it is all fully speced out.

This proposal is completely independent of traditional kv, in fact the amount of changes to Kivy is a few lines of code - the new code resides in its own module under `kivy/lang/compiler`. The new tools can be used simultaneously with traditional kv, with zero interactions between them. This means, that although I hope the proposal is merged into Kivy and that future kv will be written with the new syntax, it doesn't have to be and can still be supported as a side tool with little effect on the rest of Kivy.

But I am very excited for this new tool because I think it will solve many longstanding issues with kv, such as rule order instantiation, knowing when rules are instantiated, and unbinding. With this proposal, kv is integrated with python, so we can easily theme, by overwriting the functions that apply the kv rules. We can also unbind all, or specific  rules at will. kv rules can also be named. And much more. On a somewhat complex kv widget (7 kv rules), there was a  `2.6x` speed improvement with the compiler. Performance comparison is expected to increase with increasing kv complexity because bindings are now batched across a context.  There is also almost `200` unittests written, testing all aspects of the new syntax.

I consider the implementation complete and ready to be used, although I will of course welcome any discussion on potential improvements. This project only supports python 3.5+ and I don't ever expect to add python 2 support as the amount of effort to do that, will be pretty much the same as starting from scratch. If people like this proposal, consider it my way of motivating people to move to python 3. If merged, this code, however, will not prevent Kivy from being used in python 2.

Syntax
--------

### Intorduction

Finally, the fun part - the new syntax. Consider a traditional kv rule:

.. code-block::

    <MyWidget>:
        x: self.y

We write this as

.. code-block:: python

    class MyWidget(Widget):
        @kv()
        def apply_kv(self):
            with KvContext():
                self.x @= self.y

I'll go over all the components. `@kv()` returns a decorator which compiles the function and returns a new function that performs the bindings. We'll go over the decorator options later. `apply_kv` can be any function and may contain any python code (except as rejected by the compiler if it interferes with the bindings, which should be rare - the decorator will raise an exception at import time, when the function is compiled for that case, so it'll be obvious).

All kv rules must be under a `KvContext` and a `KvContext` may contain many kv rules, which are executed independently. However, all the initial bindings within a `KvContext` are batched and are executed when the context exits.

A rule is created using `expression_left @= expression_right`. `expression_left` and `expression_right` can be any legal python and will bind to `expression_right`, such that whenever any Kivy properties in it changes, `expression_left = expression_right` is executed.

Here are more examples of the function:

.. code-block:: python

    def apply_kv(self):
        self.widget = widget = Widget()
        offset = self.offset
        with KvContext():
            self.x @= widget.width + self.y + offset

In the example above, the value of `offset` is captured and when the rule is ever triggered, it will use that initial value. The same for `self` and `widget`. But of course, `widget.width` and `self.y` is re-evaluated every time.

Another example:

.. code-block:: python

    def apply_kv(self):
        self.widget = widget = Widget()
        with KvContext():
            offset = self.offset
            self.x @= widget.width + self.y + offset

or even

.. code-block:: python

    def apply_kv(self):
        self.widget = widget = Widget()
        with KvContext():
            offset = self.offset
            widget.width @= self.y + offset

Notice how the left side can be anything? Like in the previous examples, `self`, `widget`, and `offset` are captured and their initial values will be used whenever the rule is triggered.

As you can see, the right and left sides of the `@=` can be anything, and that line is executed initially when it is encountered, and then once the KvContext exits, the bindings will be executed and from then on, whenever the right hand property values change, the line will be executed (without the `@` sign of course). Naturally, the bindings capture the value of any locals and globals at the time the rule is encountered. In fact, to keep the bindings consistent, the compiler will raise an exception if a local or global variable used in a rule is changed between the rule definition and the context exiting. `This makes sure that code is easy to understand and reason about.`

So this example:

.. code-block:: python

    def apply_kv(self):
        widget = Widget()
        with KvContext():
            self.x @= widget.width
            widget = Widget()

will raise a parser exception because when the bindings are executed when the context exits, the `widget` is not the same as when it was encountered and used to initialize `self.x`. The exceptions are very descriptive so it's easy to fix when encountered.

Kv Rules
--------

### Explicit Rules And Events

Kv rules can be created more explicitly, which provide a lot more control over their execution. The example above:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            self.x @= self.y

can be also written as:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule():
                self.x @= self.y

The benefits is that anything under a `KvRule` is considered as **one** rule and is executed as such. Consider the following:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule():
                self.width @= self.height + 1
                self.name = 'johnny'
                self.x @= self.y

Now, whenever either `self.height` or `self.y` change, all three lines will be executed sequentially as if it's one code block, which it is.

A `KvRule` also accepts positional arguments, and will bind to whatever is provided there, this is an alternative for using the `@` syntax and allows binding to kivy **events** as follows:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule(self.on_touch_down, self.width, self.y, self.widget.height):
                self.x @= self.y + self.compute()

In the rule above, the rule will be bound to all of the provided args! That's how you can bind to kivy events, just provided it as an argument. Notice how `self.y` is provided both as an argument and using the `@=` syntax - that's okay, but it could also have been written as:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule(self.on_touch_down, self.width, self.y, self.widget.height):
                self.x = self.y + self.compute()

But either way is fine and duplications are not a problem.

Also, the above could have been written as

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule('self.on_touch_down', 'self.width', 'self.y', 'self.widget.height'):
                self.x = self.y + self.compute()

the compiler parses them identically, whether it's in string form or code form, but code form is easier as it's more IDE friendly due to auto-completion :).

In fact, you should know that the parser looks for a with statement whose context manager is literally written as `KvRule` and then modifies that line to create a rule in the compiled code. So the line `with KvRule(...)` is treated magically. That and the `with KvContext()` line and the `@=` and `^=` lines are the only objects that modify the standard python syntax and do something that is unexpected in normal python.

### Canvas and Clock Rules
In traditional kv, canvas rules are treated differently and the rules are only executed at the end of each frame - this helps with graphical performance. We have a similar construct, as opposed to rules created with the `@=` syntax or `with KvRule()`, which is the same as `with KvRule(delay=None)`, rules created using `^=` and `with KvRule(delay='canvas)`, will schedule the rules to be executed with the other graphics instructions, rather than immediately when triggered.

For example:

.. code-block:: python

    def apply_kv(self):
        with self.canvas:
            rect = Rectangle()
        with KvContext():
            rect.x ^= self.x

or:

.. code-block:: python

    def apply_kv(self):
        with self.canvas:
            rect = Rectangle()
        with KvContext():
            with KvRule(delay='canvas'):
                rect.x ^= self.x

The options between canvas and normal rules regarding binding options etc. are the same. Naturally, one rule cannot mix both canvas and normal rules, so within a rule either `@=` or `^=` must be used.

We also allow for rules to create a Clock trigger, so that when the rule bindings are triggered, instead of executing immediately, it triggers the clock event with provided delay. This allows kv rules to be batched per frame or targeted for the future. To use, you must use a explicit rule and provide a number to delay - which will be delay used when creating the clock event. E.g.

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule(delay=0):
                self.x @= self.x

will delay and batch all the rule updates for the next clock frame. The syntax is otherwise idnetical to normal kv rules.

### Loops, conditionals, and other constructs
Whenever a rule is encountered within a `KvContext`, that rules bindings will occur when the context exits. This would be the case even if the condition was False. COnsequently, a rule is now allowed under any conditional code and the parser will raise an exception. **However**, you can wrap the rule under a new `KvContext` and place that under the conditional. That makes **all** the contents under the nested `KvContext` completely isolated from the outer context it may appear in.

For example, the following examples will raise a parser exception:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            if self.height:
                self.x @= self.x

and

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            for i in range(2):
                self.x @= self.x

and even

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            try:
                print('hello')
            except Exception as e:
                self.x @= self.x

and so on.

However, it can be converted as follows and is now perfectly fine:

.. code-block:: python

    def apply_kv(self):
        if self.height:
            with KvContext():
                self.x @= self.x

and

.. code-block:: python

    def apply_kv(self):
        for i in range(2):
            with KvContext():
                self.x @= self.x

and even

.. code-block:: python

    def apply_kv(self):
        try:
            print('hello')
        except Exception as e:
            with KvContext():
                self.x @= self.x

In all cases, the `KvContext` will only be executed if the `KvContext` is executed. Although the code will of course always be compiled ahead of time when the function is originally compiled.

The following is also allowed:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            self.height @= self.width + 45
            if self.height:
                with KvContext():
                    self.x @= self.x
            self.name @= self.widget.your_name

In the above example, the rule in the inner context is completely isolated and independent from the outer context. Similarly, from the outer context's POV, it sees only two rules, the `height` and `name` rules.

For the loop example, each iteration creates a new and independent context, which are independent of each other. So the following works as expected:

.. code-block:: python

    def apply_kv(self):
        src_widgets = [Widget(), Widget()]
        target_widgets = [Widget(), Widget()]

        for i in range(2):
            with KvContext():
                target_widgets[i].x @= src_widgets[i].x

i.e. each widget's `x` is bound to the corresponding widget's `x`. This is also perfectly legally written as:

.. code-block:: python

    def apply_kv(self):
        src_widgets = [Widget(), Widget()]
        target_widgets = [Widget(), Widget()]

        for target, src in zip(target_widgets, src_widgets):
            with KvContext():
                target.x @= src.x


### Rule largs

It is sometimes desirable to get the arguments that was used to trigger the rule. E.g. when binding to `widget.on_touch_down`, the triggering touch will be dispatched. Following is how to access it in a rule:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule() as my_rule:
                print(my_rule.largs)
                self.x @= self.x

When a explicit rule is created and assigned to something, the compiler will automatically assign the captured args used when triggering the rule to the `largs` attribute of the rule. Keep in mind that `largs` may be empty, e.g. if it's dispatched during binding, so be sure to check if it's an empty tuple first.

### Rule Unbinding, named rules

A `KvRule` has some attributes and methods of interest. Specifically, `KvRule` has an `unbind_rule` method, which when called will unbind the rule and it will not be triggered again. However, it may **only** be called once the rule is fully created after the `KvContext` has exited as in the following example:

.. code-block:: python

    def apply_kv(self):
        with KvContext():
            with KvRule() as my_rule:
                self.x @= self.x
        my_rule.unbind_rule()  # goodbye rule

Similarly, the `KvContext` has a `unbind_all_rules` methods, which unbinds all the rules in the context. E.g.:

.. code-block:: python

    def apply_kv(self):
        with KvContext() as ctx:
            with KvRule():
                self.x @= self.x
            self.width @= self.height
        ctx.unbind_all_rules()  # goodbye all the rules


Every rule that is created under a context is added to that context's `rules` list in sequential order. `KvContext` also has a `named_rules` dictionary, for rules that are explicitly named. E.g.:

.. code-block:: python

    def apply_kv(self):
        with KvContext() as ctx:
            with KvRule(name='my_rule'):
                self.x @= self.x
            self.width @= self.height
        assert len(ctx.rules) == 2
        assert len(ctx.names_rules) == 1
        assert ctx.names_rules['my_rule'] is ctx.rules[0]

As can be seen from the asserts, the rules can be named and then accessed by name. They can also be accessed by index ordered by the order in which it was created.


Further specification and options
=================================

Background
-------------

The kv compiler uses AST parsing an manipulation to generate the compiled function. Given a function, if we have not already compiled a kvc file for this function, or if it's stale (source has since been changed or compile flags are different), it loads the source of the function using the inspect module and parses its AST. It then  modifies the AST and dumps it to a new `kvc` file under the `__kvcache__` directory in the same folder as the original function file.

The compiled file is then loaded and reused, making use of a runtime cache to speed up disk access. The existence of such a file will make debugging much easier as ew can just inspect it and step through it with the debugger. Although we currently do not provide any user side details on the compiled function structure.

To make sure the context the compiled function runs in is identical to the context of the original un-compiled function, every time the function is called, we set the locals/globals of the original function to the one of the compiled function.

Initially I looked into using f-strings, but it became clear that will not work.

Justification
--------------

Although using AST transformations is niche, it is justified and part of the python standard API. So it should work in e.g. pypi, although it is untested. In fact there are other projects with such a need who make use of inline AST modifications. Examples of popular projects doing that are: [pony](https://github.com/ponyorm/pony), [xpyth](https://github.com/hchasestevens/xpyth), [google pasta](https://github.com/google/pasta), and most famously [pytest](https://docs.pytest.org/en/latest/) and [ipython](https://ipython.org/). You can read more about the AST [ecosystem](https://ep2018.europython.eu/conference/talks/exploring-the-python-ast-ecosystem).

Python is also notoriously conservative when it comes to addding new syntax, e.g. there was only one minor AST change that we needed to add to support 3.7, after targeting 3.5. In addition, to prevent sudden breakage, we keep a whitelist of known AST nodes, so that when new appear the compiler will refuse to compile until the new nodes are accounted for.

I have also made liberal use of asserts everywhere in the compiler. And in general, the compiler stage is not at all optimized, but that is fine for now.

I'm hoping to add more comments to the code, but pretty much all of the algorithms I used are based on graph search or manipulations, so it's correctness can be proven. I intend to eventually add more comments with such info into the code, if accepted.

Proxying and garbage collection
-------------------------------

The idea behind using a proxy reference to a widget, is that if a widget that doesn't get garbage collected holds a reference to another widget, the other widget will also not die. We solve this by providing a parameter to the decorator which tells it to make the long living widget hold only a proxy reference to the other widgets. E.g. consider:

.. code-block:: python

    class MyWidget(Widget):
        @kv(proxy='app')
        def apply_kv(self):
            app = App.get_running_app()
            with KvContext():
                self.x @= app.x

This bind to `app`, however, because app will never die, `MyWidget` will also never die. However, in the decorator we specified `proxy='app'` - that makes the compiler use a proxy for all the references `app` holds on to. By default `proxy` is `False`, but it can be set to `True` and all will bindings will only store proxies. Or, it can be a glob style string or list of glob style strings which match the widgets that may only hold proxies. See the documentation of `kv` for more details.

A note of caution, if all the bindings use proxy references, **no one** will hold on to the kv rules and the rules will stop doing anything as soon as garbage collection runs. The solution is to store a reference to each `KvContext` - as long as that is alive, the rules are also alive.

Rebind
-------

Usage is similar to `proxy`. It indicates the widgets to which we rebind. E.g. for

.. code-block:: python

    class MyWidget(Widget):
        @kv()
        def apply_kv(self):
            with KvContext():
                self.x @= self.widget.x

if `rebind` is True, the default, then when `self.widget` changes, we rebind the rule to be triggered when then widget's `width` changes.

By default `rebind` is `True`, but it can be set to `False` and no intermediate widgets will be rebind. Or, it can be a glob style string or list of glob style strings which match the widgets that should be rebind. See the documentation of `kv` for more details. E.g. `rebind='*widget''` will rebind to `self.x @= self.widget.x`.

As opposed to traditional kv, we do not inspect the property to see if it set to rebind, because we feel that violates action at a distance, and whether a widget is rebind should be specific to the rules, and should have to be known when a property is declared. E.g. should a widget's `parent` be rebind? The answer is that we don't know and should therefore be a decision made for each compiled function.

Binding on context enter vs exit
--------------------------------

In previous examples we assumed that the bindings occur when the `KvContext` exits. Although recommended, this is but one option. By setting `bind_on_enter` in the decorator to `True`, the bindings will actually occur upon context enter. Although fully functional, this is not recommended as it is not intuitive because the bindings would happen before the rules are executed.

Nonetheless, it is offered as an option for the following reason. When binding occurs upon context exit, the bindings occur **after** the rules are executed. This means that some rules could now be stale, because when variables were set during rule execution, bindings were not in place. But, if the bindings had occurred before the rule execution, this is not a problem.

We solve this problem for the binding on exit configuration by providing the `exec_rules_after_binding` option in the `kv` decorator. If `True`, it will cause the rules to be executed again after all the bindings. This is not normally needed and reduces performance, so it defaults to `False`. But, the `bind_on_enter=True` could be used rather, rather then the default `bind_on_enter=False` combined with `exec_rules_after_binding=True`, when needed as the former is more performant than the latter case.

Globals and locals capturing within kv decorated function
---------------------------------------------------------

To be filled in

Expressions that get bound
---------------------------

To be filled in

Kv Decorable functions
-----------------------

The kv decorator does not support the decoration of closure functions. That means it can only decorate functions at the top level of a module. E.g.:

.. code-block:: python

    class MyWidget(Widget):
        @kv()
        def build_kv(...):
            pass

is allowed. As is:

.. code-block:: python

    @kv()
        def build_kv(...):
            pass


but the following is not allowed:

.. code-block:: python

    class MyWidget(Widget):
        def apply_kv(self):
            @kv()
            def build_kv(...):
                pass


Kv restrictions
---------------

Following are things that will cause the compiler to raise an exception.

* A return statement within a `KvContext`.
* A `KvRule` not under a `KvContext`.
* A `KvRule` that is under conditionally executing code such as an `if` or `for` loop, unless it's wrapped with a `KvContext`.
* Overwriting a read only captured variable (see other sections).
* A `kv` decorated function can have one, and only one decorator - the `kv` decorator.
* Nesting a `KvRule` or `KvContext` under another `KvRule`.
* A `KvRule` may not contain a function or class definition because it's unclear the meaning of such as defintion in a rule that is repeatedly executed. Also, it creates issues with ensuring the consistency of local variables.
* The `global` or `nonlocal` keyword may not occur within a function that is compiled by the `kv` compiler.
* The `del` statement is illegal within a kv rule.
* Mixing canvas and normal or clock kv syntax within a rule.

Manual kv compiler
---------------------

In addition to the kv compiler described above and below, we also provide a manual compiler for debugging and unofficial usage and in order to have a complete implementation. Following is a comparison using the kv compiler and manual compilation:

.. code-block:: python

    class ManualKvWidget(Widget):
        def apply_kv(self):
            ctx = KvParserContext()

            def manage_val(*largs):
                self.x = self.y + 512
            manage_val()

            # will bind to `self.y`.
            rule = KvParserRule('self.y + 512')
            rule.callback = manage_val
            rule.callback_name = manage_val.__name__
            ctx.add_rule(rule)

            kv_apply_manual(ctx, self.apply_kv, locals(), globals())

vs. the automatic compiler, which would look like as follows:

.. code-block:: python

    class ManualKvWidget(Widget):
        @kv()
        def apply_kv(self):
            with KvContext():
                self.x @= self.y + 512

Both examples effect a compilation, but the decorator version happens automatically and is more efficient.

Requirements for property binding
----------------------------------

The following are required methods to exist on a object, in order for binding to occur on the object's property. We `fbind` and `fbind_proxy` return `Falsy` if it fails and does not raise an error - we therefore do not check at all whether the property is a Kivy property before binding. Duck typing FTW.

* Must have the following functions
* `fbind` or `fbind_proxy` or both, depending on the `proxy` setting.
* `unbind_uid`. If the former exists, `unbind_uid` will be assumed to exist and not checked before usage.

For code correctness, we also assume that calling `fbind` will have no side effects.

Some simple rules and style guide
---------------------------------

To be filled in

* All kv rules within a context are *always* bound and cannot therefore be under any conditional or loop etc.
* To place a kv rule under a conditional or loop, wrap it with a new context and place the context under the conditional.
* By default no proxies are used. If proxies are used and all objects are proxied, the rules will die immediately as no one will have a reference to them. So make sure to only proxy objects that are not needed to keep the rule alive. Additionally, as long as someone has a direct ref to the context, the contexts and its rules will not die.
* The start and end of a KvContext is special: that's where the bindings occur, depending on the setting, so whatever variable is referenced by a rule, that variable must exist at the start or end of the context depending on the setting. Similarly, the value of the variables that are bound, are the values of the variables at that fence point. If the variables are changed during the rule, during the initialization, all the code is executed, it's just the binding that captures it.
* clearly we can use locals to change a local, but we disallow it on principle the easy way
* kv rules are not finalized until the context exists. But `largs` is always available.
* locals cannot be None is used in binding.
* Use proxy for widgets that never die, to prevent them from keeping other widgets from dying. But, make sure to store the KvContext somewhere if all widgets store only proxies, otherwise, if no one holds on to the kv rules, it will be garbage collected.
* During binding, local and global variables that are potentially bound are assumed to not be None as for performance reasons it's not practical to check each local whether it's None. But deeper variables, e.g. `widget` in `self.widget.x` will be inspected and only bound if not None.

Explain that the `with KvRule` and `with KvContext` are magic, not real context manager. Actually entering will raise error.

style guide: try to keep kv code from mixing with other code
save the ctx

Theming Demo
=============

Following is a demo of how theming may work with this proposal. Consider the following two classes, the first may be considered to have a default theme, the second wants to overwrite the theme.

.. code-block:: python

    class MyWidgetTheme(Widget):

        def __init__(self, **kwargs):
            super(MyWidgetTheme, self).__init__(__no_builder=True, **kwargs)
            self.build_kv()

        @kv()
        def build_kv(self):
            with KvContext():
                self.x @= self.y

    class MyWidgetThemeMaterialDesign(MyWidgetTheme):
        @kv()
        def build_kv(self):
            with KvContext():
                self.x @= self.width

When run, we get the following:

.. code-block:: python

    >>> w = MyWidgetTheme()
    >>> print(w.x, w.y, w.width)
    0 0 100
    >>> w.y = 46
    >>> print(w.x, w.y, w.width)
    46 46 100

    >>> themed_widget = MyWidgetThemeMaterialDesign()
    >>> print(themed_widget.x, themed_widget.y, themed_widget.width)
    100 0 100
    >>> themed_widget.y = 43
    >>> print(themed_widget.x, themed_widget.y, themed_widget.width)
    100 43 100
    >>> themed_widget.width = 25
    >>> print(themed_widget.x, themed_widget.y, themed_widget.width)
    25 43 25


As can be seen, the two "themed" widgets, each apply their own rule. In other words, we can use the full power of python inheritance with kv rules for theming.

Example of full widget with traditional kv vs the proposed syntax.
===================================================================

Following is the traditional description of `Label`'s kv rule

.. code-block::

    <Label>:
        canvas:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                texture: self.texture
                size: self.texture_size
                pos: int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)

Here it is with the proposed new syntax.

.. code-block:: python

    @kv()
    def apply_kv(self):
        with self.canvas:
            Color(1, 1, 1, 1)
            rect = Rectangle()

        with KvContext():
            rect.texture @= self.texture
            rect.size @= self.texture_size
            rect.pos @= int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)

Following is the traditional description of `Button`'s kv rule

.. code-block::

    <-Button,-ToggleButton>:
        state_image: self.background_normal if self.state == 'normal' else self.background_down
        disabled_image: self.background_disabled_normal if self.state == 'normal' else self.background_disabled_down
        canvas:
            Color:
                rgba: self.background_color
            BorderImage:
                border: self.border
                pos: self.pos
                size: self.size
                source: self.disabled_image if self.disabled else self.state_image
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                texture: self.texture
                size: self.texture_size
                pos: int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)

Here it is with the proposed new syntax.

.. code-block:: python

    @kv()
    def apply_kv(self):
        with self.canvas:
            color = Color()
            border = BorderImage()
            Color(1, 1, 1, 1)
            rect = Rectangle()

        with KvContext():
            self.state_image @= self.background_normal if self.state == 'normal' else self.background_down
            self.disabled_image @= self.background_disabled_normal if self.state == 'normal' else self.background_disabled_down
            color.rgba @= self.background_color

            border.border @= self.border
            border.pos @= self.pos
            bordersize @= self.size
            border.source @= self.disabled_image if self.disabled else self.state_image

            rect.texture @= self.texture
            rect.size @= self.texture_size
            rect.pos @= int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)

As one can, they look very similar, but the python syntax can be more easily integrated into the rest of the widget's python code.

Things to work out
===================

* To compile a function, we need to be able to load the source using the inspect module. Are the situations where the source code is not available? If we cannot find source code, should we just provide a way/place to look for previously compiled files and use that instead? How exactly will that work?
* I chose to save each compiled function into its own file. I don't really see issues with that, and there's also no clear reasonable way currently to combine all the compiled functions of a file into a single file. So unless this becomes an issue, single file per function seems reasonable.
* If we were to use this for theming, we will need to come up with standard function names that apply the kv rules, and perhaps a variable that keeps the kv context for ease of rebinding.
