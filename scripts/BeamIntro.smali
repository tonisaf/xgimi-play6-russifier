.class public final Lcom/xgimi/atmosphere/settings/data/introduce/BeamIntro;
.super Ljava/lang/Object;
.method public static decorate(Lcom/xgimi/view/cell/Cell;)V
    .locals 6
    new-instance v0, Lcom/xgimi/view/cell/layout/FrameLayout;
    invoke-direct {v0}, Lcom/xgimi/view/cell/layout/FrameLayout;-><init>()V
    invoke-virtual {p0, v0}, Lcom/xgimi/view/cell/Cell;->setLayout(Lcom/xgimi/view/cell/Layout;)Lcom/xgimi/view/cell/Cell;
    new-instance v0, Lcom/xgimi/view/cell/Cell;
    invoke-direct {v0}, Lcom/xgimi/view/cell/Cell;-><init>()V
    new-instance v1, Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/ColorComponent;-><init>()V
    const v2, -16777216
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/ColorComponent;->setColor(I)Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/component/TextComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/TextComponent;-><init>()V
    const-string v2, ""
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -1
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 1
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 200
    const v3, 72
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 135
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 352
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginTop(I)Lcom/xgimi/view/cell/Layout$Params;
    invoke-virtual {p0, v0, v1}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;
    new-instance v0, Lcom/xgimi/view/cell/Cell;
    invoke-direct {v0}, Lcom/xgimi/view/cell/Cell;-><init>()V
    new-instance v1, Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/ColorComponent;-><init>()V
    const v2, -16777216
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/ColorComponent;->setColor(I)Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/component/TextComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/TextComponent;-><init>()V
    const-string v2, ""
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -1
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 1
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 405
    const v3, 42
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 135
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 454
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginTop(I)Lcom/xgimi/view/cell/Layout$Params;
    invoke-virtual {p0, v0, v1}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;
    new-instance v0, Lcom/xgimi/view/cell/Cell;
    invoke-direct {v0}, Lcom/xgimi/view/cell/Cell;-><init>()V
    new-instance v1, Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/ColorComponent;-><init>()V
    const v2, -1
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/ColorComponent;->setColor(I)Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/component/TextComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/TextComponent;-><init>()V
    const-string v2, ""
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -1
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 1
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 160
    const v3, 64
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 205
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 640
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginTop(I)Lcom/xgimi/view/cell/Layout$Params;
    invoke-virtual {p0, v0, v1}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;
    new-instance v0, Lcom/xgimi/view/cell/Cell;
    invoke-direct {v0}, Lcom/xgimi/view/cell/Cell;-><init>()V
    new-instance v1, Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/ColorComponent;-><init>()V
    const v2, 0
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/ColorComponent;->setColor(I)Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/component/TextComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/TextComponent;-><init>()V
    const-string v2, "Atmosphere"
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -1
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 62
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 420
    const v3, 82
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 140
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 350
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginTop(I)Lcom/xgimi/view/cell/Layout$Params;
    invoke-virtual {p0, v0, v1}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;
    new-instance v0, Lcom/xgimi/view/cell/Cell;
    invoke-direct {v0}, Lcom/xgimi/view/cell/Cell;-><init>()V
    new-instance v1, Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/ColorComponent;-><init>()V
    const v2, 0
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/ColorComponent;->setColor(I)Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/component/TextComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/TextComponent;-><init>()V
    const-string v2, "Заставки для уютной атмосферы"
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -6710887
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 28
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 500
    const v3, 46
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 140
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 454
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginTop(I)Lcom/xgimi/view/cell/Layout$Params;
    invoke-virtual {p0, v0, v1}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;
    new-instance v0, Lcom/xgimi/view/cell/Cell;
    invoke-direct {v0}, Lcom/xgimi/view/cell/Cell;-><init>()V
    new-instance v1, Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/ColorComponent;-><init>()V
    const v2, 0
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/ColorComponent;->setColor(I)Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/component/TextComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/TextComponent;-><init>()V
    const-string v2, "Открыть"
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -16777216
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 36
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 155
    const v3, 58
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 212
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 646
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginTop(I)Lcom/xgimi/view/cell/Layout$Params;
    invoke-virtual {p0, v0, v1}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;
    return-void
.end method
