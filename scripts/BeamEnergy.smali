.class public final Lcom/xgimi/atmosphere/settings/data/introduce/BeamEnergy;
.super Ljava/lang/Object;
.method public static decorate(Lcom/xgimi/view/cell/Cell;)V
    .locals 5
    new-instance v0, Lcom/xgimi/view/cell/Cell;
    invoke-direct {v0}, Lcom/xgimi/view/cell/Cell;-><init>()V
    new-instance v1, Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/ColorComponent;-><init>()V
    const v2, -14277082
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/ColorComponent;->setColor(I)Lcom/xgimi/view/cell/component/ColorComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/component/TextComponent;
    invoke-direct {v1}, Lcom/xgimi/view/cell/component/TextComponent;-><init>()V
    const-string v2, ""
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -14277082
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 1
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 322
    const v3, 82
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 124
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 46
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
    const-string v2, "Энергосбережение"
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -1
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 24
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 322
    const v3, 38
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 124
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 45
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
    const-string v2, "Яркость снижена для экономии"
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setText(Ljava/lang/String;)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, -3355444
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setColor(I)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 20
    int-to-float v2, v2
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setTextSize(F)Lcom/xgimi/view/cell/component/TextComponent;
    const v2, 19
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/component/TextComponent;->setGravity(I)Lcom/xgimi/view/cell/component/TextComponent;
    invoke-virtual {v0, v1}, Lcom/xgimi/view/cell/Cell;->addComponent(Lcom/xgimi/view/cell/Component;)Lcom/xgimi/view/cell/Cell;
    new-instance v1, Lcom/xgimi/view/cell/layout/FrameLayout$Params;
    const v2, 322
    const v3, 52
    const v4, 51
    invoke-direct {v1, v2, v3, v4}, Lcom/xgimi/view/cell/layout/FrameLayout$Params;-><init>(III)V
    const v2, 124
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginLeft(I)Lcom/xgimi/view/cell/Layout$Params;
    const v2, 84
    invoke-virtual {v1, v2}, Lcom/xgimi/view/cell/Layout$Params;->setMarginTop(I)Lcom/xgimi/view/cell/Layout$Params;
    invoke-virtual {p0, v0, v1}, Lcom/xgimi/view/cell/Cell;->addCell(Lcom/xgimi/view/cell/Cell;Lcom/xgimi/view/cell/Layout$Params;)Lcom/xgimi/view/cell/Cell;
    return-void
.end method
