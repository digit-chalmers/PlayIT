// Auto-generated from videocontainer.html.
// DO NOT EDIT.

library videocontainer;

import 'dart:html' as autogenerated;
import 'dart:svg' as autogenerated_svg;
import 'package:web_ui/web_ui.dart' as autogenerated;
import 'package:web_ui/observe/observable.dart' as __observe;
import 'package:web_ui/web_ui.dart';



const SERVER_URL = 'http://129.16.187.87:8080/youTubeInTheHubbServer/video/';

class VideoComponent extends WebComponent {
  /** Autogenerated from the template. */

  autogenerated.ScopedCssMapper _css;

  /** This field is deprecated, use getShadowRoot instead. */
  get _root => getShadowRoot("videocontainer");
  static final __shadowTemplate = new autogenerated.DocumentFragment.html('''
        <div>
          <button>Upvote!</button><br>
          <span>(imgurl: <img>)</span>
          <span></span>
          <span></span>
        </div>
      ''');
  autogenerated.ButtonElement __e1;
  autogenerated.ImageElement __e2;
  autogenerated.SpanElement __e4, __e6;
  autogenerated.Template __t;

  void created_autogenerated() {
    var __root = createShadowRoot("videocontainer");
    setScopedCss("videocontainer", new autogenerated.ScopedCssMapper({"videocontainer":"[is=\"videocontainer\"]"}));
    _css = getScopedCss("videocontainer");
    __t = new autogenerated.Template(__root);
    __root.nodes.add(__shadowTemplate.clone(true));
    __e1 = __root.nodes[1].nodes[1];
    __t.listen(__e1.onClick, ($event) { upvote(); });
    __e2 = __root.nodes[1].nodes[4].nodes[1];
    __t.oneWayBind(() => imgurl, (e) { if (__e2.src != e) __e2.src = e; }, false, true);
    __e4 = __root.nodes[1].nodes[6];
    var __binding3 = __t.contentBind(() => title, false);
    __e4.nodes.addAll([new autogenerated.Text('(title: '),
        __binding3,
        new autogenerated.Text(')')]);
    __e6 = __root.nodes[1].nodes[8];
    var __binding5 = __t.contentBind(() => votes, false);
    __e6.nodes.addAll([new autogenerated.Text('(votes: '),
        __binding5,
        new autogenerated.Text(')')]);
    __t.create();
  }

  void inserted_autogenerated() {
    __t.insert();
  }

  void removed_autogenerated() {
    __t.remove();
    __t = __e1 = __e2 = __e4 = __e6 = null;
  }

  /** Original code from the component. */

  VideoComponent() {
    @observable
    int votes = 0;
    @observable
    String imgurl = this.getimgurl(0);
    @observable
    String title = "";
  }

  String getimgurl(int videoNumber) {
    HttpRequest.getString(SERVER_URL + "showQueue").then((response) {
      List parsedList = parse(response);
      return parsedList[videoNumber]['url'];
    });
  }

  void upvote() {
    votes++;
  }
}
//# sourceMappingURL=xclickcounter.dart.map